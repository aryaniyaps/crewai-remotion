import {interpolate, spring, SpringConfig, useCurrentFrame} from 'remotion';
import type {EasingFunction} from 'remotion';
import {Easing} from 'remotion';

// ── Motion style → spring preset ──

export type MotionStyle = 'snappy' | 'smooth' | 'kinetic';

interface SpringPreset {
  config: Partial<SpringConfig>;
  staggerFrames: number;
  entryDurationFrames: number;
  exitDurationFrames: number;
}

const PRESETS: Record<MotionStyle, SpringPreset> = {
  snappy: {
    config: {damping: 20, stiffness: 200, mass: 0.8},
    staggerFrames: 3,
    entryDurationFrames: 14,
    exitDurationFrames: 10,
  },
  smooth: {
    config: {damping: 30, stiffness: 120, mass: 1.2},
    staggerFrames: 6,
    entryDurationFrames: 20,
    exitDurationFrames: 14,
  },
  kinetic: {
    config: {damping: 12, stiffness: 170, mass: 0.6},
    staggerFrames: 2,
    entryDurationFrames: 10,
    exitDurationFrames: 6,
  },
};

export const getMotionPreset = (style: MotionStyle): SpringPreset =>
  PRESETS[style] ?? PRESETS.snappy;

// ── Composed progress (one normalized value drives opacity + translate + scale) ──

export interface ComposedProgress {
  opacity: number;
  translateY: number;
  scale: number;
}

/**
 * Compute a single composed progress value [0,1], then derive opacity,
 * translate, and scale from it. Prevents elements animating out of sync.
 */
export const composedProgress = (
  frame: number,
  entryStart: number,
  entryDuration: number,
): number =>
  interpolate(frame, [entryStart, entryStart + entryDuration], [0, 1], {
    extrapolateRight: 'clamp',
    extrapolateLeft: 'clamp',
  });

export const composedEntry = (progress: number): ComposedProgress => ({
  opacity: interpolate(progress, [0, 0.3, 1], [0, 0, 1]),
  translateY: interpolate(progress, [0, 1], [40, 0]),
  scale: interpolate(progress, [0, 1], [0.92, 1]),
});

export const composedExit = (progress: number): ComposedProgress => ({
  opacity: interpolate(progress, [0, 0.7, 1], [1, 0, 0]),
  translateY: interpolate(progress, [0, 1], [0, -30]),
  scale: interpolate(progress, [0, 0.3, 1], [1, 0.98, 0.94]),
});

// ── Bezier easing ──

/** Entrances: gentle overshoot, natural settle. */
export const entranceEase: EasingFunction = Easing.bezier(0.22, 1, 0.36, 1);

/** Exits: accelerate out, no linger. */
export const exitEase: EasingFunction = Easing.in(Easing.cubic);

// ── Spring helpers ──

/**
 * Stagger spring for multi-element entry. Each element at `index` delays
 * by `index * staggerFrames` frames.
 */
export const staggeredSpring = (
  frame: number,
  index: number,
  style: MotionStyle,
  delayFrames: number = 0,
): number => {
  const {staggerFrames, config} = getMotionPreset(style);
  return spring({
    frame: frame - delayFrames - index * staggerFrames,
    fps: 30,
    config,
  });
};

/**
 * Scale punch for emphasis words — brief overshoot then settle.
 */
export const emphasisPunch = (frame: number, peakFrame: number): number => {
  const t = frame - peakFrame;
  // Only active for 8 frames around peak
  if (t < -4 || t > 4) return 1;
  return spring({
    frame: t + 4,
    from: 1,
    to: 1.08,
    fps: 30,
    config: {damping: 15, stiffness: 200},
  });
};

// ── Cut-on-action velocity ──

/**
 * Compute the frame within an exit animation where peak velocity occurs.
 * Default: ~70% through the exit duration.
 */
export const cutOnActionFrame = (
  exitStart: number,
  exitDuration: number,
  fraction: number = 0.7,
): number => exitStart + Math.floor(exitDuration * fraction);

// ── Motion intensity limits ──

export type MotionIntensity = 'low' | 'medium' | 'high';

export const MOTION_INTENSITY_CAPS: Record<
  MotionIntensity,
  {maxLayers: number; maxStaggerDepth: number}
> = {
  low: {maxLayers: 2, maxStaggerDepth: 2},
  medium: {maxLayers: 3, maxStaggerDepth: 3},
  high: {maxLayers: 4, maxStaggerDepth: 4},
};

// ── CameraMotionBlur config ──

export const DEFAULT_MOTION_BLUR = {
  shutterAngle: 180,
  samples: 3,
} as const;

// ── React hooks ──


/**
 * Entry progress hook — returns normalized [0,1] progress over `durationFrames`
 * using a spring. Use for composed entry animations.
 */
export const useEnterProgress = (durationFrames: number = 14, delayFrames: number = 0, style: MotionStyle = 'snappy'): number => {
  const frame = useCurrentFrame();
  const {config} = getMotionPreset(style);
  return spring({
    frame: frame - delayFrames,
    fps: 30,
    config,
    durationInFrames: durationFrames,
  });
};

/**
 * Exit progress hook — returns normalized [0,1] progress.
 * Call with frame relative to exit start.
 */
export const useExitProgress = (exitStart: number, durationFrames: number = 10, style: MotionStyle = 'snappy'): number => {
  const frame = useCurrentFrame();
  const {config} = getMotionPreset(style);
  return spring({
    frame: frame - exitStart,
    fps: 30,
    config: {...config, damping: 20},
    durationInFrames: durationFrames,
  });
};

// ═══════════════════════════════════════════════════════════════════════
//  Motion Graphics Utilities
// ═══════════════════════════════════════════════════════════════════════

/**
 * Generate an SVG path string for a wave that undulates over time.
 * Returns a cubic bezier path across the viewport width.
 */
export const wavePath = (
  frame: number,
  amplitude: number = 30,
  frequency: number = 0.03,
  phase: number = 0,
  width: number = 1080,
  baseY: number = 960,
  fps: number = 30,
): string => {
  const step = 60;
  const points: Array<{x: number; y: number}> = [];
  for (let x = 0; x <= width; x += step) {
    const y = baseY + Math.sin(x * frequency + frame * 0.05 + phase) * amplitude;
    points.push({x, y});
  }

  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const cp_x = (points[i].x + points[i + 1].x) / 2;
    path += ` Q ${points[i].x} ${points[i].y}, ${cp_x} ${(points[i].y + points[i + 1].y) / 2}`;
  }
  path += ` T ${width + 200} ${baseY}`;
  return path;
};

/**
 * Compute per-particle state for staggered particle fields.
 */
export interface ParticleState {
  x: number;
  y: number;
  scale: number;
  opacity: number;
}

export const particleSpring = (
  frame: number,
  index: number,
  config: {
    count: number;
    spread: number;
    speed: number;
    style?: MotionStyle;
  },
): ParticleState => {
  const {spread, speed, style = 'snappy'} = config;
  const seed = index * 137.508; // golden angle for pseudo-random
  const stagger = staggeredSpring(frame, index, style, 0);

  const angle = (seed % (Math.PI * 2));
  const radius = spread * 0.5 * stagger;
  const baseX = Math.cos(angle) * spread * 0.4;
  const baseY = Math.sin(angle) * spread * 0.5;

  const drift = frame * speed * 0.02;
  const x = baseX + Math.cos(drift + seed * 0.7) * spread * 0.15;
  const y = baseY + Math.sin(drift + seed * 0.3) * spread * 0.25;

  const scale = interpolate(stagger, [0, 1], [0, 1.2]);
  const opacity = interpolate(stagger, [0, 0.3, 1], [0, 0.8, 0.6]);

  return {x, y, scale, opacity};
};

/**
 * Generate an SVG path string by interpolating between shape paths.
 * Shapes supported: 'circle', 'triangle', 'square', 'star', 'hexagon'.
 */
const SHAPE_PATHS: Record<string, (cx: number, cy: number, r: number) => string> = {
  circle: (cx, cy, r) => {
    return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx} ${cy + r} A ${r} ${r} 0 1 1 ${cx} ${cy - r} Z`;
  },
  triangle: (cx, cy, r) => {
    const h = r * 1.5;
    return `M ${cx} ${cy - r} L ${cx + r * 0.866} ${cy + r * 0.5} L ${cx - r * 0.866} ${cy + r * 0.5} Z`;
  },
  square: (cx, cy, r) => {
    return `M ${cx - r} ${cy - r} L ${cx + r} ${cy - r} L ${cx + r} ${cy + r} L ${cx - r} ${cy + r} Z`;
  },
  star: (cx, cy, r) => {
    const points = 5;
    const innerR = r * 0.4;
    let d = '';
    for (let i = 0; i < points * 2; i++) {
      const radius = i % 2 === 0 ? r : innerR;
      const angle = (Math.PI / 2) * -1 + (Math.PI / points) * i;
      const x = cx + Math.cos(angle) * radius;
      const y = cy + Math.sin(angle) * radius;
      d += (i === 0 ? 'M ' : 'L ') + `${x} ${y} `;
    }
    return d + 'Z';
  },
  hexagon: (cx, cy, r) => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 6;
      pts.push(`${cx + Math.cos(angle) * r} ${cy + Math.sin(angle) * r}`);
    }
    return `M ${pts.join(' L ')} Z`;
  },
};

export const morphPath = (
  progress: number,
  shapes: string[],
  cx: number = 540,
  cy: number = 960,
  r: number = 100,
): string => {
  const count = shapes.length;
  if (count === 0) return '';

  const segment = 1 / count;
  const segIndex = Math.min(Math.floor(progress / segment), count - 1);
  const segProgress = (progress - segIndex * segment) / segment;

  const fromShape = shapes[segIndex];
  const toShape = shapes[(segIndex + 1) % count];

  const fromPath = (SHAPE_PATHS[fromShape] ?? SHAPE_PATHS.circle)(cx, cy, r);
  const toPath = (SHAPE_PATHS[toShape] ?? SHAPE_PATHS.circle)(cx, cy, r);

  // Simple linear interpolation of path points by decomposing and blending
  const fromPts = extractPathPoints(fromPath);
  const toPts = extractPathPoints(toPath);

  if (fromPts.length === 0 || toPts.length === 0) return fromPath;

  // Normalise point counts by repeating the larger set
  const maxLen = Math.max(fromPts.length, toPts.length);
  const blended = [];
  for (let i = 0; i < maxLen; i++) {
    const fi = i % fromPts.length;
    const ti = i % toPts.length;
    const x = interpolate(segProgress, [0, 1], [fromPts[fi].x, toPts[ti].x]);
    const y = interpolate(segProgress, [0, 1], [fromPts[fi].y, toPts[ti].y]);
    blended.push({x, y});
  }

  let d = `M ${blended[0].x} ${blended[0].y}`;
  for (let i = 1; i < blended.length; i++) {
    d += ` L ${blended[i].x} ${blended[i].y}`;
  }
  d += ' Z';
  return d;
};

/** Extract {x,y} points from a simple M/L/Z SVG path */
function extractPathPoints(d: string): Array<{x: number; y: number}> {
  const pts: Array<{x: number; y: number}> = [];
  const matches = d.matchAll(/[ML]\s*([\d.-]+)\s+([\d.-]+)/g);
  for (const m of matches) {
    pts.push({x: parseFloat(m[1]), y: parseFloat(m[2])});
  }
  return pts;
}

/**
 * Compute parallax offset for a depth plane.
 * Returns {x, y} to apply as translate.
 */
export const parallaxOffset = (
  frame: number,
  plane: 'back' | 'mid' | 'front',
  speed: number = 1,
): {x: number; y: number} => {
  const multipliers = {back: 0.3, mid: 0.6, front: 1.2};
  const mult = multipliers[plane] * speed;
  const x = Math.sin(frame * 0.008) * 8 * mult;
  const y = Math.cos(frame * 0.012) * 5 * mult;
  return {x, y};
};

/**
 * Camera shake / handheld motion offset.
 * Returns {x, y, rotation} for subtle instability.
 */
export const cameraShake = (
  frame: number,
  intensity: 'low' | 'medium' | 'high' = 'low',
): {x: number; y: number; rotation: number} => {
  const amps = {low: 3, medium: 6, high: 12};
  const amp = amps[intensity];
  const seed1 = Math.sin(frame * 1.7 + 1) * Math.cos(frame * 0.9 + 3);
  const seed2 = Math.cos(frame * 1.3 + 2) * Math.sin(frame * 1.1 + 5);
  const seed3 = Math.sin(frame * 0.7 + 4) * Math.cos(frame * 1.5 + 1);

  return {
    x: seed1 * amp,
    y: seed2 * amp * 0.7,
    rotation: seed3 * amp * 0.015,
  };
};

/**
 * Camera motion transform for push_in / pull_out / pan / tilt.
 * Returns {scale, translateX, translateY} for CSS transform.
 */
export const cameraMotionTransform = (
  frame: number,
  motion: 'none' | 'push_in' | 'pull_out' | 'pan_left' | 'pan_right' | 'tilt_up' | 'tilt_down' | 'handheld',
  durationFrames: number = 90,
): {scale: number; translateX: number; translateY: number} => {
  const t = frame / Math.max(durationFrames, 1);
  switch (motion) {
    case 'push_in':
      return {
        scale: interpolate(t, [0, 1], [1, 1.08]),
        translateX: 0,
        translateY: 0,
      };
    case 'pull_out':
      return {
        scale: interpolate(t, [0, 1], [1.06, 1]),
        translateX: 0,
        translateY: 0,
      };
    case 'pan_left':
      return {
        scale: 1,
        translateX: interpolate(t, [0, 1], [0, -20]),
        translateY: 0,
      };
    case 'pan_right':
      return {
        scale: 1,
        translateX: interpolate(t, [0, 1], [0, 20]),
        translateY: 0,
      };
    case 'tilt_up':
      return {
        scale: 1,
        translateX: 0,
        translateY: interpolate(t, [0, 1], [0, -15]),
      };
    case 'tilt_down':
      return {
        scale: 1,
        translateX: 0,
        translateY: interpolate(t, [0, 1], [0, 15]),
      };
    case 'none':
    default:
      return {scale: 1, translateX: 0, translateY: 0};
  }
};
