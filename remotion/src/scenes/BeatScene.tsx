import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import type {ThemeTokens} from '../design/tokens';
import {
  useEnterProgress,
  composedEntry,
  staggeredSpring,
  emphasisPunch,
  cameraShake,
  cameraMotionTransform,
} from '../design/motion';
import {MotionGraphicsLayer} from '../layers/MotionGraphicsLayer';
import {ParallaxLayer} from '../layers/ParallaxLayer';
import {BackgroundLayer} from '../layers/BackgroundLayer';
import type {MotionGraphic} from '../catalog/motion-graphics';

export const BeatScene: React.FC<{
  theme: ThemeTokens;
  headline: string;
  subhead?: string;
  sceneType: string;
  backgroundVariant?: string;
  layout?: string;
  imagePath?: string | null;
  showHeadline?: boolean;
  motionGraphics?: MotionGraphic[];
  motionIntent?: string;
  motionIntensity?: 'low' | 'medium' | 'high';
  parallaxDepth?: number;
  cameraMotion?: 'none' | 'push_in' | 'pull_out' | 'pan_left' | 'pan_right' | 'tilt_up' | 'tilt_down' | 'handheld';
  durationFrames?: number;
}> = ({
  theme,
  headline,
  subhead,
  sceneType,
  backgroundVariant,
  layout,
  imagePath,
  showHeadline = true,
  motionGraphics,
  motionIntent,
  motionIntensity = 'medium',
  parallaxDepth = 0,
  cameraMotion,
  durationFrames = 90,
}) => {
  const frame = useCurrentFrame();

  // Auto-resolve motion graphics from intent if none explicitly provided
  const resolvedMotionGraphics: MotionGraphic[] = useMemo(() => {
    if (motionGraphics && motionGraphics.length > 0) return motionGraphics;
    if (!motionIntent) return [];

    const defaults: Record<string, MotionGraphic[]> = {
      enter_up: [
        {id: 'auto-particles', type: 'particles', config: {count: 20, speed: 0.4, spread: 200, color: 'primary', size: 3}},
        {id: 'auto-ring-pulse', type: 'ring_pulse', config: {count: 3, maxRadius: 180, interval: 10, color: 'accent'}},
      ],
      fade_in: [
        {id: 'auto-wave', type: 'wave', config: {amplitude: 15, frequency: 0.3, layers: 2, color: 'primary'}},
        {id: 'auto-data-flow', type: 'data_flow', config: {lines: 6, speed: 0.5, direction: 'right', color: 'secondary'}},
      ],
      scale_burst: [
        {id: 'auto-burst', type: 'energy_burst', config: {lines: 14, maxLength: 180, color: 'accent'}},
        {id: 'auto-particles-burst', type: 'particles', config: {count: 30, speed: 0.8, spread: 250, color: 'accent', size: 4}},
      ],
      slide_in: [
        {id: 'auto-ripple', type: 'ring_pulse', config: {count: 3, maxRadius: 200, interval: 12, color: 'secondary'}},
        {id: 'auto-grid-pulse', type: 'grid_pulse', config: {cells: 4, cellSize: 50, pulseSpeed: 1.2, color: 'primary'}},
      ],
    };
    return defaults[motionIntent] ?? [];
  }, [motionGraphics, motionIntent]);

  const progress = useEnterProgress(
    14,
    4,
    (theme.motion_style as 'snappy' | 'smooth' | 'kinetic') ?? 'snappy',
  );
  const entry = composedEntry(progress);

  // Determine alignment from layout token
  const isLeft = layout?.includes('left');
  const isRight = layout?.includes('right');
  const alignItems = isLeft ? 'flex-start' : isRight ? 'flex-end' : 'center';
  const textAlign = isLeft ? 'left' : isRight ? 'right' : 'center';

  // Accent color for subhead/stat emphasis
  const accent =
    sceneType === 'StatBeat' || sceneType === 'HookBeat'
      ? theme.accent
      : theme.primary;

  // Font tier by scene type
  const fontSize =
    sceneType === 'HookBeat' ? 76 : sceneType === 'StatBeat' ? 88 : 52;
  const fontWeight =
    sceneType === 'HookBeat' || sceneType === 'StatBeat' ? 800 : 700;

  // Stat beat: scale burst
  const statScale =
    sceneType === 'StatBeat'
      ? interpolate(frame % 15, [0, 7, 15], [0.9, 1.05, 1])
      : 1;

  // Beat progress 0-1 for motion graphics layer
  const beatProgress = frame / Math.max(durationFrames, 1);

  // Camera motion transform
  const cameraTransform = cameraMotion
    ? cameraMotionTransform(frame, cameraMotion, durationFrames)
    : {scale: 1, translateX: 0, translateY: 0};

  // Handheld shake if applicable
  const shake = cameraMotion === 'handheld' ? cameraShake(frame, 'low') : {x: 0, y: 0, rotation: 0};

  // Kinetic typography: stagger headline characters
  const headlineChars = useMemo(() => {
    if (!showHeadline) return null;
    const chars = headline.split('');
    return chars.map((char, i) => {
      const stagger = staggeredSpring(frame, i, (theme.motion_style as 'snappy' | 'smooth' | 'kinetic') ?? 'snappy', 2);
      const punch = sceneType === 'HookBeat' ? emphasisPunch(frame, 8 + i * 1) : 1;
      const charOpacity = stagger;
      const charY = interpolate(stagger, [0, 1], [30, 0]);
      return (
        <span
          key={i}
          style={{
            display: 'inline-block',
            opacity: charOpacity,
            transform: `translateY(${charY}px) scale(${punch})`,
            whiteSpace: char === ' ' ? 'pre' : undefined,
          }}
        >
          {char}
        </span>
      );
    });
  }, [frame, headline, showHeadline, theme.motion_style, sceneType]);

  // Build subhead element conditionally
  const subheadEl = subhead ? (
    <div
      style={{
        marginTop: 20,
        fontSize: 30,
        color: accent,
        fontFamily: theme.font_body,
        fontWeight: 500,
        opacity: entry.opacity * 0.9,
      }}
    >
      {subhead}
    </div>
  ) : null;

  return (
    <AbsoluteFill
      style={{
        scale: String(cameraTransform.scale),
        translate: `${cameraTransform.translateX + shake.x}px ${cameraTransform.translateY + shake.y}px`,
        rotate: `${shake.rotation}deg`,
      }}
    >
      <BackgroundLayer theme={theme} variant={backgroundVariant} />

      {/* Motion graphics layer — replaces static illustrations */}
      {resolvedMotionGraphics.length > 0 && (
        <MotionGraphicsLayer
          theme={theme}
          motionGraphics={resolvedMotionGraphics}
          beatProgress={beatProgress}
          frame={frame}
          intensity={motionIntensity}
        />
      )}

      {/* Parallax wrapper for text content */}
      <ParallaxLayer speed={parallaxDepth}>
        {/* Text content */}
        <AbsoluteFill
          style={{
            padding: 64,
            justifyContent: resolvedMotionGraphics.length > 0 ? 'flex-end' : 'center',
            alignItems,
            paddingBottom: resolvedMotionGraphics.length > 0 ? 240 : 64,
          }}
        >
          <div
            style={{
              transform: `translateY(${entry.translateY}px) scale(${
                entry.scale * statScale
              })`,
              opacity: entry.opacity,
              maxWidth: 900,
              textAlign,
            }}
          >
            <div
              style={{
                fontSize,
                fontWeight,
                color: '#ffffff',
                lineHeight: 1.05,
                fontFamily: theme.font_heading,
                letterSpacing: '-0.02em',
              }}
            >
              {headlineChars}
            </div>
            {subheadEl}
          </div>
        </AbsoluteFill>
      </ParallaxLayer>
    </AbsoluteFill>
  );
};
