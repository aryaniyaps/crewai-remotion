export type MotionStyle = 'snappy' | 'smooth' | 'kinetic';
export type Texture = 'none' | 'grain' | 'paper';

export type ThemeTokens = {
  primary: string;
  secondary: string;
  accent: string;
  surface: string;
  caption_highlight: string;
  font_heading: string;
  font_body: string;
  motion_style: MotionStyle;
  texture: Texture;
};

export const defaultTheme: ThemeTokens = {
  primary: '#FF3366',
  secondary: '#1A1A2E',
  accent: '#FFD700',
  surface: '#0F0F14',
  caption_highlight: '#39E508',
  font_heading: 'Space Grotesk',
  font_body: 'Space Grotesk',
  motion_style: 'snappy' as const,
  texture: 'grain' as const,
};
