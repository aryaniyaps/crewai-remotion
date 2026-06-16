import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ThemeTokens} from '../design/tokens';
import {
  staggeredSpring,
  wavePath,
  particleSpring,
  morphPath,
  type MotionIntensity,
} from '../design/motion';
import type {MotionGraphic, MotionGraphicType} from '../catalog/motion-graphics';

export const MotionGraphicsLayer: React.FC<{
  theme: ThemeTokens;
  motionGraphics: MotionGraphic[];
  beatProgress: number;
  frame: number;
  intensity?: MotionIntensity;
}> = ({theme, motionGraphics, beatProgress, frame, intensity = 'medium'}) => {
  const {fps, width, height} = useVideoConfig();

  const activeGraphics = useMemo(
    () =>
      motionGraphics.filter((g) => {
        const entryOk = g.entry_frame === undefined || frame >= g.entry_frame;
        const exitOk = g.exit_frame === undefined || frame < g.exit_frame;
        return entryOk && exitOk;
      }),
    [motionGraphics, frame],
  );

  if (activeGraphics.length === 0) return null;

  const resolveColor = (token: string) => {
    switch (token) {
      case 'accent': return theme.accent;
      case 'secondary': return theme.secondary;
      case 'surface': return theme.surface;
      case 'primary':
      default: return theme.primary;
    }
  };

  const capIntensity = intensity === 'high' ? 4 : intensity === 'medium' ? 3 : 2;
  const capped = activeGraphics.slice(0, capIntensity);

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {capped.map((g) => (
        <GraphicRenderer
          key={g.id}
          graphic={g}
          frame={frame}
          beatProgress={beatProgress}
          fps={fps}
          width={width}
          height={height}
          resolveColor={resolveColor}
          motionStyle={(theme.motion_style as 'snappy' | 'smooth' | 'kinetic') ?? 'snappy'}
        />
      ))}
    </AbsoluteFill>
  );
};

// ── Individual graphic renderers ──

const GraphicRenderer: React.FC<{
  graphic: MotionGraphic;
  frame: number;
  beatProgress: number;
  fps: number;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({graphic, frame, beatProgress, fps, width, height, resolveColor, motionStyle}) => {
  const config = graphic.config ?? {};

  switch (graphic.type) {
    case 'particles':
      return <ParticlesGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    case 'wave':
      return <WaveGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} />;
    case 'ring_pulse':
      return <RingPulseGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    case 'geometric_morph':
      return <MorphGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} />;
    case 'energy_burst':
      return <BurstGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    case 'orbital':
      return <OrbitalGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} />;
    case 'data_flow':
      return <DataFlowGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} fps={fps} />;
    case 'grid_pulse':
      return <GridPulseGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} fps={fps} />;
    case 'text_shatter':
      return <TextShatterGraphic frame={frame} config={config} beatProgress={beatProgress} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    case 'glow_trail':
      return <GlowTrailGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    case 'kinetic_type_zoom':
      return <KineticTypeZoomGraphic frame={frame} config={config} width={width} height={height} resolveColor={resolveColor} motionStyle={motionStyle} />;
    default:
      return null;
  }
});

// ═══════════════════════════════════════════════════════════════════════
//  Particles — floating dots with staggered drift
// ═══════════════════════════════════════════════════════════════════════

const ParticlesGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, width, height, resolveColor, motionStyle}) => {
  const count = (config.count as number) ?? 30;
  const speed = (config.speed as number) ?? 0.5;
  const spread = (config.spread as number) ?? 300;
  const colorToken = (config.color as string) ?? 'primary';
  const size = (config.size as number) ?? 4;
  const color = resolveColor(colorToken);

  const particles = useMemo(() => {
    const items: Array<{key: number; x: number; y: number; s: number; o: number}> = [];
    for (let i = 0; i < count; i++) {
      const state = particleSpring(frame, i, {count, spread, speed, style: motionStyle});
      items.push({
        key: i,
        x: width / 2 + state.x,
        y: height / 2 + state.y,
        s: state.scale * size,
        o: state.opacity,
      });
    }
    return items;
  }, [frame, count, spread, speed, motionStyle, width, height, size]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {particles.map((p) => (
        <circle key={p.key} cx={p.x} cy={p.y} r={p.s} fill={color} opacity={p.o} />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Wave — undulating SVG path
// ═══════════════════════════════════════════════════════════════════════

const WaveGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
}> = React.memo(({frame, config, width, height, resolveColor}) => {
  const amplitude = (config.amplitude as number) ?? 30;
  const frequency = (config.frequency as number) ?? 0.5;
  const layers = ((config.layers as number) ?? 2);
  const colorToken = (config.color as string) ?? 'primary';
  const color = resolveColor(colorToken);

  const lines = useMemo(() => {
    const result: Array<{d: string; opacity: number; y: number}> = [];
    for (let i = 0; i < layers; i++) {
      const baseY = height * (0.5 + i * 0.15);
      const d = wavePath(frame, amplitude * (1 - i * 0.25), frequency * 0.03, i * 1.5, width, baseY, 30);
      result.push({d, opacity: 0.4 - i * 0.12, y: baseY});
    }
    return result;
  }, [frame, amplitude, frequency, layers, width, height]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {lines.map((line, i) => (
        <path key={i} d={line.d} fill="none" stroke={color} strokeWidth={2} opacity={line.opacity} />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Ring Pulse — expanding concentric circles (sonar)
// ═══════════════════════════════════════════════════════════════════════

const RingPulseGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, width, height, resolveColor, motionStyle}) => {
  const ringCount = (config.count as number) ?? 3;
  const maxRadius = (config.maxRadius as number) ?? 250;
  const interval = (config.interval as number) ?? 15;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);

  const cx = width / 2;
  const cy = height / 2;

  const rings = useMemo(() => {
    const items: Array<{key: number; r: number; opacity: number; strokeWidth: number}> = [];
    for (let i = 0; i < ringCount; i++) {
      const ringFrame = frame - i * interval;
      if (ringFrame < 0) continue;
      const r = interpolate(ringFrame % (interval * ringCount), [0, interval * ringCount], [5, maxRadius]);
      const opacity = interpolate(r, [5, maxRadius], [0.6, 0]);
      const strokeWidth = interpolate(r, [5, maxRadius], [3, 0.5]);
      items.push({key: i, r, opacity, strokeWidth});
    }
    return items;
  }, [frame, ringCount, maxRadius, interval]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {rings.map((ring) => (
        <circle key={ring.key} cx={cx} cy={cy} r={ring.r} fill="none" stroke={color} strokeWidth={ring.strokeWidth} opacity={ring.opacity} />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Geometric Morph — SVG shape morphing
// ═══════════════════════════════════════════════════════════════════════

const MorphGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
}> = React.memo(({frame, config, width, height, resolveColor}) => {
  const size = (config.size as number) ?? 120;
  const speed = (config.speed as number) ?? 1;
  const shapes = (config.shapes as string[]) ?? ['circle', 'triangle', 'square'];
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);

  const cycleFrames = 120 / speed;
  const progress = (frame % cycleFrames) / cycleFrames;

  const d = morphPath(progress, shapes, width / 2, height / 2, size / 2);

  const entrySpring = spring({frame, fps: 30, config: {damping: 20, stiffness: 200}});

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={3}
        opacity={entrySpring * 0.5}
        style={{transformOrigin: `${width / 2}px ${height / 2}px`, scale: String(entrySpring)}}
      />
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Energy Burst — radial lines exploding outward
// ═══════════════════════════════════════════════════════════════════════

const BurstGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, width, height, resolveColor, motionStyle}) => {
  const lines = (config.lines as number) ?? 16;
  const maxLength = (config.maxLength as number) ?? 200;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);

  const cx = width / 2;
  const cy = height / 2;

  const burstItems = useMemo(() => {
    const items: Array<{key: number; x2: number; y2: number; opacity: number}> = [];
    for (let i = 0; i < lines; i++) {
      const angle = (Math.PI * 2 * i) / lines;
      const spr = staggeredSpring(frame, i, motionStyle, 0);
      const len = spr * maxLength;
      const fade = interpolate(spr, [0, 0.6, 1], [1, 0.8, 0]);
      items.push({
        key: i,
        x2: cx + Math.cos(angle) * len,
        y2: cy + Math.sin(angle) * len,
        opacity: fade * 0.6,
      });
    }
    return items;
  }, [frame, lines, maxLength, motionStyle, cx, cy]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {burstItems.map((item) => (
        <line key={item.key} x1={cx} y1={cy} x2={item.x2} y2={item.y2} stroke={color} strokeWidth={2} opacity={item.opacity} />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Orbital — concentric orbiting dots (atomic model)
// ═══════════════════════════════════════════════════════════════════════

const OrbitalGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
}> = React.memo(({frame, config, width, height, resolveColor}) => {
  const rings = (config.rings as number) ?? 3;
  const dotsPerRing = (config.dots as number) ?? 5;
  const baseRadius = (config.radius as number) ?? 120;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);

  const cx = width / 2;
  const cy = height / 2;

  const orbitalItems = useMemo(() => {
    const items: Array<{key: string; cx: number; cy: number; r: number; opacity: number}> = [];
    for (let ring = 0; ring < rings; ring++) {
      const radius = baseRadius + ring * 40;
      const orbitSpeed = 1 - ring * 0.2;
      for (let d = 0; d < dotsPerRing; d++) {
        const angle = (Math.PI * 2 * d) / dotsPerRing + frame * 0.02 * orbitSpeed;
        items.push({
          key: `r${ring}-d${d}`,
          cx: cx + Math.cos(angle) * radius,
          cy: cy + Math.sin(angle) * radius * 0.4, // Elliptical
          r: 4 - ring * 0.5,
          opacity: 0.6 - ring * 0.12,
        });
      }
    }
    return items;
  }, [frame, rings, dotsPerRing, baseRadius, cx, cy]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {/* Orbit paths */}
      {Array.from({length: rings}).map((_, i) => {
        const radius = baseRadius + i * 40;
        return (
          <ellipse key={`orbit-${i}`} cx={cx} cy={cy} rx={radius} ry={radius * 0.4} fill="none" stroke={color} strokeWidth={0.5} opacity={0.15} />
        );
      })}
      {/* Orbiting dots */}
      {orbitalItems.map((dot) => (
        <circle key={dot.key} cx={dot.cx} cy={dot.cy} r={dot.r} fill={color} opacity={dot.opacity} />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Data Flow — flowing data stream lines
// ═══════════════════════════════════════════════════════════════════════

const DataFlowGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  fps: number;
}> = React.memo(({frame, config, width, height, resolveColor, fps}) => {
  const lineCount = (config.lines as number) ?? 10;
  const speed = (config.speed as number) ?? 1;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);
  const direction = (config.direction as string) ?? 'right';

  const lines = useMemo(() => {
    const items: Array<{key: number; x1: number; y1: number; x2: number; y2: number; opacity: number}> = [];
    const isHorizontal = direction === 'right' || direction === 'left';
    for (let i = 0; i < lineCount; i++) {
      const offset = (frame * speed + i * 40) % (isHorizontal ? width + 200 : height + 200);
      let x1: number, y1: number, x2: number, y2: number;
      if (isHorizontal) {
        const dir = direction === 'right' ? 1 : -1;
        x1 = offset * dir - 200 * dir;
        y1 = (height / (lineCount + 1)) * (i + 1);
        x2 = x1 + 80 * dir;
        y2 = y1;
      } else {
        const dir = direction === 'down' ? 1 : -1;
        y1 = offset * dir - 200 * dir;
        x1 = (width / (lineCount + 1)) * (i + 1);
        y2 = y1 + 80 * dir;
        x2 = x1;
      }
      const opacity = interpolate(offset, [0, 100], [0.1, 0.5]);
      items.push({key: i, x1, y1, x2, y2, opacity: Math.max(0, Math.min(0.5, opacity))});
    }
    return items;
  }, [frame, lineCount, speed, direction, width, height]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {lines.map((l) => (
        <line key={l.key} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke={color} strokeWidth={1.5} opacity={l.opacity} strokeLinecap="round" />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Grid Pulse — pulsing grid squares
// ═══════════════════════════════════════════════════════════════════════

const GridPulseGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  fps: number;
}> = React.memo(({frame, config, width, height, resolveColor, fps}) => {
  const cells = (config.cells as number) ?? 4;
  const cellSize = (config.cellSize as number) ?? 60;
  const pulseSpeed = (config.pulseSpeed as number) ?? 1;
  const colorToken = (config.color as string) ?? 'primary';
  const color = resolveColor(colorToken);

  const gridWidth = cells * cellSize;
  const offsetX = (width - gridWidth) / 2;
  const offsetY = (height - gridWidth) / 2;

  const gridItems = useMemo(() => {
    const items: Array<{key: string; x: number; y: number; opacity: number}> = [];
    for (let row = 0; row < cells; row++) {
      for (let col = 0; col < cells; col++) {
        const index = row * cells + col;
        const pulse = Math.sin(frame * 0.05 * pulseSpeed + index * 0.3) * 0.5 + 0.5;
        items.push({
          key: `g${row}-${col}`,
          x: offsetX + col * cellSize,
          y: offsetY + row * cellSize,
          opacity: 0.1 + pulse * 0.25,
        });
      }
    }
    return items;
  }, [frame, cells, cellSize, pulseSpeed, offsetX, offsetY]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {gridItems.map((item) => (
        <rect
          key={item.key}
          x={item.x}
          y={item.y}
          width={cellSize - 2}
          height={cellSize - 2}
          fill={color}
          opacity={item.opacity}
          rx={4}
        />
      ))}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Text Shatter — characters fly apart and reassemble
// ═══════════════════════════════════════════════════════════════════════

const TextShatterGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  beatProgress: number;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, beatProgress, width, height, resolveColor, motionStyle}) => {
  const count = (config.count as number) ?? 30;
  const spread = (config.spread as number) ?? 150;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);
  const cx = width / 2;
  const cy = height / 2;

  const fragments = useMemo(() => {
    const items: Array<{key: string; x: number; y: number; size: number; angle: number}> = [];
    // Create fragment-like particles: thin rects at varied angles
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.3;
      const dist = spread * (0.4 + Math.random() * 0.6);
      items.push({
        key: `ts-${i}`,
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        size: 2 + Math.random() * 8,
        angle: Math.random() * Math.PI * 2,
      });
    }
    return items;
  }, [count, spread]);

  // Use beatProgress to control scatter → assemble
  // beatProgress 0 = scattered, beatProgress 1 = assembled
  const scatterFactor = motionStyle === 'kinetic'
    ? Math.pow(1 - beatProgress, 3)
    : 1 - beatProgress;

  const pulseAlpha = 0.3 + beatProgress * 0.5;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {fragments.map((frag, i) => {
        const dx = frag.x * scatterFactor;
        const dy = frag.y * scatterFactor;
        const sx = cx + dx;
        const sy = cy + dy;
        return (
          <rect
            key={frag.key}
            x={sx - frag.size / 2}
            y={sy - 1}
            width={frag.size}
            height={3}
            fill={color}
            opacity={0.2 + pulseAlpha * 0.5 * (1 - Math.abs(i / count - 0.5) * 2)}
            rx={1}
            transform={`rotate(${frag.angle * (1 - scatterFactor) * 180 / Math.PI}, ${sx}, ${sy})`}
          />
        );
      })}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Glow Trail — particles following a path with luminous afterglow
// ═══════════════════════════════════════════════════════════════════════

const GlowTrailGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, width, height, resolveColor, motionStyle}) => {
  const count = (config.count as number) ?? 20;
  const trailLength = (config.trail as number) ?? 8;
  const speed = (config.speed as number) ?? 0.6;
  const pathRadius = (config.pathRadius as number) ?? 120;
  const colorToken = (config.color as string) ?? 'accent';
  const color = resolveColor(colorToken);
  const cx = width / 2;
  const cy = height / 2;

  const trailItems = useMemo(() => {
    const items: Array<{key: string; trail: Array<{x: number; y: number; alpha: number; r: number}>}> = [];
    for (let i = 0; i < count; i++) {
      const phaseOffset = (Math.PI * 2 * i) / count;
      const angle = phaseOffset + frame * 0.02 * speed;
      const r = pathRadius * (0.6 + 0.4 * Math.sin(angle * 1.5 + phaseOffset));
      const px = cx + Math.cos(angle) * r;
      const py = cy + Math.sin(angle) * r * 0.6;

      const trail: Array<{x: number; y: number; alpha: number; r: number}> = [];
      for (let t = 0; t < trailLength; t++) {
        const trailAngle = angle - t * 0.08;
        const tr = pathRadius * (0.6 + 0.4 * Math.sin(trailAngle * 1.5 + phaseOffset));
        trail.push({
          x: cx + Math.cos(trailAngle) * tr,
          y: cy + Math.sin(trailAngle) * tr * 0.6,
          alpha: (1 - t / trailLength) * 0.6,
          r: 3 - t * 0.3,
        });
      }
      items.push({key: `gt-${i}`, trail});
    }
    return items;
  }, [count, trailLength, speed, pathRadius, frame, cx, cy]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {trailItems.map((item) =>
        item.trail.map((dot, di) => (
          <circle
            key={`${item.key}-${di}`}
            cx={dot.x}
            cy={dot.y}
            r={dot.r}
            fill={color}
            opacity={dot.alpha * 0.8}
          />
        ))
      )}
    </svg>
  );
});

// ═══════════════════════════════════════════════════════════════════════
//  Kinetic Type Zoom — headline-scale emphasis pulse
// ═══════════════════════════════════════════════════════════════════════

const KineticTypeZoomGraphic: React.FC<{
  frame: number;
  config: Record<string, unknown>;
  width: number;
  height: number;
  resolveColor: (t: string) => string;
  motionStyle: 'snappy' | 'smooth' | 'kinetic';
}> = React.memo(({frame, config, width, height, resolveColor, motionStyle}) => {
  const maxScale = (config.scale as number) ?? 1.3;
  const frequency = (config.frequency as number) ?? 2;
  const ringCount = (config.rings as number) ?? 3;
  const colorToken = (config.color as string) ?? 'primary';
  const color = resolveColor(colorToken);
  const cx = width / 2;
  const cy = height / 2;

  // Oscillating scale: rapid in, sustain, snap back
  const phase = frame * 0.05 * frequency;
  const oscillation = Math.abs(Math.sin(phase));
  const baseScale = 1 + (maxScale - 1) * oscillation;
  // Apply motion style curve
  const scaleCurve = motionStyle === 'kinetic'
    ? Math.pow(oscillation, 0.5)
    : motionStyle === 'snappy'
    ? oscillation < 0.3 ? oscillation / 0.3 : 1 - (oscillation - 0.3) / 0.7
    : oscillation;
  const scale = 1 + (maxScale - 1) * scaleCurve;

  const ringItems = useMemo(() => {
    const items: Array<{r: number; opacity: number; dashOffset: number}> = [];
    for (let i = 0; i < ringCount; i++) {
      const ringPhase = phase + (i * Math.PI * 2) / ringCount;
      const ringOsc = Math.abs(Math.sin(ringPhase));
      items.push({
        r: 40 + ringOsc * 80 + i * 30,
        opacity: 0.15 + ringOsc * 0.25,
        dashOffset: frame * 2 + i * 40,
      });
    }
    return items;
  }, [ringCount, phase, frame]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {ringItems.map((ring, i) => (
        <circle
          key={`ktz-${i}`}
          cx={cx}
          cy={cy}
          r={ring.r * scale}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="12 8"
          strokeDashoffset={ring.dashOffset}
          opacity={ring.opacity}
        />
      ))}
    </svg>
  );
});
