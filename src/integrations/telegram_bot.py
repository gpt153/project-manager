"""
Telegram Bot Integration.

This module implements the Telegram bot interface for the Project Manager.
Users can interact with the orchestrator through natural language in Telegram.
"""

import logging
from uuid import UUID

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.agent.orchestrator_agent import run_orchestrator
from src.database.models import Project, ProjectStatus
from src.services.approval_gate import get_pending_gates
from src.services.vision_generator import (
    check_conversation_completeness,
    generate_vision_document,
    vision_document_to_markdown,
)
from src.services.workflow_orchestrator import (
    advance_workflow,
    get_workflow_state,
    handle_approval_response,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class OrchestratorTelegramBot:
    """
    Telegram bot for Project Manager.

    Provides natural language interface for:
    - Brainstorming project ideas
    - Vision document generation
    - Workflow management
    - Approval gates
    """

    def __init__(self, token: str, db_session_maker):
        """
        Initialize the Telegram bot.

        Args:
            token: Telegram bot token
            db_session_maker: Database session maker
        """
        self.application = Application.builder().token(token).build()
        self.db_session_maker = db_session_maker

        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("continue", self.continue_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command - initiate new project.

        Args:
            update: Telegram update
            context: Handler context
        """
        chat_id = update.effective_chat.id

        async with self.db_session_maker() as session:
            # Create new project
            project = Project(
                name=f"Project_{chat_id}",
                status=ProjectStatus.BRAINSTORMING,
                telegram_chat_id=chat_id,
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)

            # Store project ID in context
            context.chat_data["project_id"] = str(project.id)

        welcome_message = (
            "👋 Welcome to the Project Manager!\n\n"
            "I'm here to help you build your software project from idea to implementation.\n\n"
            "**Let's start brainstorming:**\n"
            "Tell me about your project idea. What do you want to build?\n\n"
            "I'll ask you questions to understand your vision, then we'll create a "
            "clear vision document and start building together!"
        )

        await update.message.reply_text(welcome_message, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.

        Args:
            update: Telegram update
            context: Handler context
        """
        help_text = (
            "**Project Manager Help**\n\n"
            "**Commands:**\n"
            "/start - Start a new project\n"
            "/status - Check current project status\n"
            "/continue - Continue to next workflow phase\n"
            "/help - Show this help message\n\n"
            "**How it works:**\n"
            "1. 💭 **Brainstorm** - Tell me your idea\n"
            "2. 📝 **Vision** - I'll create a clear vision document\n"
            "3. 🎯 **Plan** - We'll create an implementation plan\n"
            "4. 💻 **Build** - I'll implement the features\n"
            "5. ✅ **Validate** - We'll test everything\n\n"
            "Just chat with me naturally, and I'll guide you through each step!"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /status command - show current workflow status.

        Args:
            update: Telegram update
            context: Handler context
        """
        project_id_str = context.chat_data.get("project_id")

        if not project_id_str:
            await update.message.reply_text("No active project. Use /start to begin a new project.")
            return

        project_id = UUID(project_id_str)

        async with self.db_session_maker() as session:
            state = await get_workflow_state(session, project_id)

            status_message = (
                f"**Project Status**\n\n"
                f"📍 Current Phase: {state.current_phase}\n"
                f"➡️ Next Action: {state.next_action}\n"
            )

            if state.awaiting_approval:
                status_message += "\n⏳ Waiting for your approval"

            await update.message.reply_text(status_message, parse_mode="Markdown")

    async def continue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /continue command - advance workflow to next phase.

        Args:
            update: Telegram update
            context: Handler context
        """
        project_id_str = context.chat_data.get("project_id")

        if not project_id_str:
            await update.message.reply_text("No active project. Use /start to begin a new project.")
            return

        project_id = UUID(project_id_str)

        async with self.db_session_maker() as session:
            success, message = await advance_workflow(session, project_id)

            if success:
                await update.message.reply_text(f"✅ {message}", parse_mode="Markdown")

                # Check for pending approval gates
                await self._check_and_send_approval_gates(update, project_id, session)
            else:
                await update.message.reply_text(f"❌ Error: {message}", parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle user messages - process through orchestrator agent.

        Args:
            update: Telegram update
            context: Handler context
        """
        user_message = update.message.text
        project_id_str = context.chat_data.get("project_id")

        if not project_id_str:
            await update.message.reply_text("Please start a new project with /start first.")
            return

        project_id = UUID(project_id_str)

        # Show typing indicator
        await update.message.chat.send_action("typing")

        async with self.db_session_maker() as session:
            # Run orchestrator agent
            response = await run_orchestrator(project_id, user_message, session)

            # Send response
            await update.message.reply_text(response, parse_mode="Markdown")

            # Check if conversation is complete enough for vision doc
            completeness = await check_conversation_completeness(session, project_id)

            if completeness.is_ready:
                # Offer to generate vision document
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ Generate Vision Doc", callback_data="generate_vision"
                        ),
                        InlineKeyboardButton("💬 Keep Brainstorming", callback_data="keep_talking"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "🎉 I think we have enough information to create a vision document!\n\n"
                    "Would you like me to generate it now, or continue brainstorming?",
                    reply_markup=reply_markup,
                )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle inline button callbacks.

        Args:
            update: Telegram update
            context: Handler context
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        project_id_str = context.chat_data.get("project_id")

        if not project_id_str:
            await query.edit_message_text("Session expired. Please /start again.")
            return

        project_id = UUID(project_id_str)

        async with self.db_session_maker() as session:
            # Handle vision generation
            if callback_data == "generate_vision":
                await self._generate_and_send_vision(query, project_id, session)

            elif callback_data == "keep_talking":
                await query.edit_message_text("Great! Keep telling me about your project. 💭")

            # Handle approval gates
            elif callback_data.startswith("approve:"):
                gate_id = UUID(callback_data.split(":")[1])
                await self._handle_approval(query, gate_id, True, session)

            elif callback_data.startswith("reject:"):
                gate_id = UUID(callback_data.split(":")[1])
                await self._handle_approval(query, gate_id, False, session)

    async def _generate_and_send_vision(self, query, project_id: UUID, session) -> None:
        """Generate vision document and send to user"""
        await query.edit_message_text("📝 Generating vision document...")

        try:
            vision_doc = await generate_vision_document(session, project_id)

            # Convert to markdown
            markdown = vision_document_to_markdown(vision_doc)

            # Send vision document
            await query.message.reply_text(
                f"**Your Vision Document**\n\n{markdown}",
                parse_mode="Markdown",
            )

            # Create approval gate
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Approve", callback_data=f"approve:vision_{project_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Needs Changes", callback_data=f"reject:vision_{project_id}"
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                "📋 Please review the vision document.\n\n"
                "Does this accurately capture your project vision?",
                reply_markup=reply_markup,
            )

        except ValueError as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def _handle_approval(self, query, gate_id: UUID, approved: bool, session) -> None:
        """Handle approval gate response"""
        success, message = await handle_approval_response(session, gate_id, approved)

        if success:
            await query.edit_message_text(f"✅ {message}", parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ {message}", parse_mode="Markdown")

    async def _check_and_send_approval_gates(
        self, update: Update, project_id: UUID, session
    ) -> None:
        """Check for pending approval gates and send them"""
        pending_gates = await get_pending_gates(session, project_id)

        for gate in pending_gates:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve:{gate.id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject:{gate.id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            context = gate.context or {}
            title = context.get("title", "Approval Required")
            summary = context.get("summary", "Please review")

            await update.message.reply_text(
                f"**{title}**\n\n{summary}",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

    def run(self) -> None:
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
