export interface ProjectColor {
  primary: string;
  light: string;
  veryLight: string;
  text: string;
}

/**
 * Generate a deterministic color palette from a project ID
 * Uses HSL color space for pleasant, accessible colors
 */
export function generateProjectColor(projectId: string): ProjectColor {
  // Simple hash function to get a consistent number from the ID
  let hash = 0;
  for (let i = 0; i < projectId.length; i++) {
    hash = projectId.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32bit integer
  }

  // Generate hue from hash (0-360 degrees)
  const hue = Math.abs(hash % 360);

  // Fixed saturation and lightness for good visibility
  const saturation = 70; // 70% - vibrant but not overwhelming
  const primaryLightness = 50; // 50% - good contrast

  // Generate color variations
  const primary = `hsl(${hue}, ${saturation}%, ${primaryLightness}%)`;
  const light = `hsl(${hue}, ${saturation - 10}%, ${primaryLightness + 35}%)`; // Lighter for sidebar
  const veryLight = `hsl(${hue}, ${saturation - 20}%, ${primaryLightness + 45}%)`; // Very light for chat background

  // Determine text color based on lightness (ensure readable contrast)
  const text = primaryLightness > 50 ? '#000000' : '#FFFFFF';

  return {
    primary,
    light,
    veryLight,
    text,
  };
}

/**
 * Check if a color has sufficient contrast ratio (WCAG AA standard)
 * Note: Unused helper function for future enhancement
 */
export function hasGoodContrast(_foreground: string, _background: string): boolean {
  // Simplified contrast check - in production, use a proper library
  // This is a basic implementation for demonstration
  return true; // Placeholder - our generated colors should have good contrast
}
