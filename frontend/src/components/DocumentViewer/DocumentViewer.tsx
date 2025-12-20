import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './DocumentViewer.css';

interface DocumentViewerProps {
  projectId: string;
  documentType: 'vision' | 'plan';
  onClose: () => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ projectId, documentType, onClose }) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);

        const endpoint = documentType === 'vision'
          ? `/api/documents/vision/${projectId}`
          : `/api/documents/plans/${projectId}`;

        const response = await fetch(endpoint);

        if (!response.ok) {
          throw new Error(`Failed to fetch ${documentType} document`);
        }

        const text = await response.text();
        setContent(text);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [projectId, documentType]);

  const handleOpenInNewTab = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="document-viewer-overlay" onClick={onClose}>
        <div className="document-viewer-modal" onClick={(e) => e.stopPropagation()}>
          <div className="document-viewer-header">
            <h2>Loading {documentType} document...</h2>
            <button onClick={onClose} className="close-button">×</button>
          </div>
          <div className="document-viewer-content loading">
            <div className="loader">Loading...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-viewer-overlay" onClick={onClose}>
        <div className="document-viewer-modal" onClick={(e) => e.stopPropagation()}>
          <div className="document-viewer-header">
            <h2>Error</h2>
            <button onClick={onClose} className="close-button">×</button>
          </div>
          <div className="document-viewer-content error">
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="document-viewer-overlay" onClick={onClose}>
      <div className="document-viewer-modal" onClick={(e) => e.stopPropagation()}>
        <div className="document-viewer-header">
          <h2>{documentType === 'vision' ? 'Vision Document' : 'Implementation Plan'}</h2>
          <div className="header-actions">
            <button onClick={handleOpenInNewTab} className="action-button">
              Open in New Tab
            </button>
            <button onClick={onClose} className="close-button">×</button>
          </div>
        </div>
        <div className="document-viewer-content">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};
