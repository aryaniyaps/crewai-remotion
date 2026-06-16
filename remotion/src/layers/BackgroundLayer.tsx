import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import type {ThemeTokens} from '../design/tokens';

/**
 * BackgroundLayer — mesh gradient base with optional noise grain.
 *
 * Creates depth via subtle gradient drift. Hook beats use primary-dominant;
 * body beats use secondary-dominant; CTA beats fade to surface.
 */
export const BackgroundLayer: React.FC<{
  theme: ThemeTokens;
  variant?: string;
}> = ({theme, variant = 'primary'}) => {
  const frame = useCurrentFrame();

  // Slow gradient drift for living-background feel
  const driftX = interpolate(frame % 240, [0, 120, 240], [0, 25, 0]);
  const driftY = interpolate(frame % 300, [0, 150, 300], [0, 15, 0]);

  // Pick dominant color by variant
  const dominantColor =
    variant === 'primary'
      ? theme.primary
      : variant === 'surface'
        ? theme.surface
        : theme.secondary;

  return (
    <AbsoluteFill
      style={{
        background: `
          radial-gradient(
            circle at ${30 + driftX * 0.3}% ${25 + driftY * 0.2}%,
            ${dominantColor}44 0%,
            ${theme.surface} 70%
          ),
          radial-gradient(
            circle at ${70 - driftX * 0.2}% ${60 + driftY * 0.15}%,
            ${theme.accent}22 0%,
            transparent 50%
          )
        `,
        // Grain texture via CSS noise (film grain simulation)
        ...(theme.texture === 'grain'
          ? {
              backgroundImage: `
                radial-gradient(
                  circle at ${30 + driftX * 0.3}% ${25 + driftY * 0.2}%,
                  ${dominantColor}44 0%,
                  ${theme.surface} 70%
                ),
                radial-gradient(
                  circle at ${70 - driftX * 0.2}% ${60 + driftY * 0.15}%,
                  ${theme.accent}22 0%,
                  transparent 50%
                ),
                url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.08'/%3E%3C/svg%3E")
              `,
              backgroundBlendMode: 'normal, normal, overlay',
            }
          : {}),
      }}
    />
  );
};
