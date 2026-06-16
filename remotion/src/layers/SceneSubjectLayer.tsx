import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useVideoConfig} from 'remotion';
import type {ThemeTokens} from '../design/tokens';

export type SubjectEntityKind =
  | 'data_center'
  | 'city'
  | 'power_grid'
  | 'chip'
  | 'globe_network'
  | 'generic';

type MotionIntensity = 'low' | 'medium' | 'high';

type SubjectLayerProps = {
  theme: ThemeTokens;
  headline: string;
  subhead?: string;
  sceneType: string;
  imagePath?: string | null;
  generatedAssetPath?: string | null;
  illustrationId?: string | null;
  layout?: string;
  motionIntensity?: MotionIntensity;
  frame: number;
  durationFrames: number;
};

type EntityProps = {
  theme: ThemeTokens;
  frame: number;
  motionScale: number;
  width: number;
  height: number;
};

const SUBJECT_TOP = 210;
const SUBJECT_HEIGHT = 820;
const CAPTION_SAFE_TOP = 1320;
const IMAGE_FRAME_HEIGHT = 780;
const LIGHT_PHASES = [0, 0.9, 1.8, 2.7, 3.6] as const;
const RACK_X = [116, 294, 472, 650] as const;
const CITY_BUILDINGS = [
  {x: 86, y: 380, w: 116, h: 220, tone: 0},
  {x: 222, y: 300, w: 134, h: 300, tone: 1},
  {x: 378, y: 235, w: 150, h: 365, tone: 2},
  {x: 552, y: 330, w: 126, h: 270, tone: 1},
  {x: 704, y: 270, w: 112, h: 330, tone: 0},
] as const;
const CHIP_PINS = [0, 1, 2, 3, 4, 5, 6, 7] as const;
const ORBIT_NODES = [0, 1, 2, 3, 4, 5] as const;

const intensityScale = (intensity: MotionIntensity = 'medium'): number => {
  if (intensity === 'low') return 0.65;
  if (intensity === 'high') return 1.35;
  return 1;
};

export const deriveEntityKind = (
  headline: string,
  subhead: string | undefined,
  sceneType: string,
  illustrationId?: string | null,
): SubjectEntityKind => {
  const text = `${illustrationId ?? ''} ${headline} ${subhead ?? ''} ${sceneType}`.toLowerCase();

  if (/(data[ _-]?center|datacenter|server|servers|cloud|compute|computing|infrastructure|rack|database|tech giant|tech giants|data giant|data giants|data\b)/.test(text)) {
    return 'data_center';
  }

  if (/(energy|electric|electricity|power|grid|battery|batteries|renewable|solar|wind|voltage)/.test(text)) {
    return 'power_grid';
  }

  if (/(internet|network|networks|world|global|planet|globe|data flow|data flows|traffic|bandwidth|fiber|fibre|connected|connection|trade route)/.test(text)) {
    return 'globe_network';
  }

  if (/(ai|artificial intelligence|semiconductor|chip|chips|gpu|processor|silicon|circuit)/.test(text)) {
    return 'chip';
  }

  if (/(building|buildings|city|cities|country|countries|economy|economies|gdp|urban|nation|nations|market|markets|government|governments)/.test(text)) {
    return 'city';
  }

  return 'generic';
};

export const SceneSubjectLayer: React.FC<SubjectLayerProps> = ({
  theme,
  headline,
  subhead,
  sceneType,
  imagePath,
  generatedAssetPath,
  illustrationId,
  layout,
  motionIntensity = 'medium',
  frame,
  durationFrames,
}) => {
  const {width, height, fps} = useVideoConfig();
  const motionScale = intensityScale(motionIntensity);
  const entityKind = useMemo(
    () => deriveEntityKind(headline, subhead, sceneType, illustrationId),
    [headline, illustrationId, sceneType, subhead],
  );

  const entry = spring({
    frame: frame - 3,
    fps,
    config: {damping: 18, stiffness: 120, mass: 0.9},
    durationInFrames: 22,
  });
  const opacity = interpolate(entry, [0, 0.35, 1], [0, 0.85, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const enterY = interpolate(entry, [0, 1], [120, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const enterScale = interpolate(entry, [0, 1], [0.82, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame / 22) * 10 * motionScale;
  const driftX = Math.sin(frame / 48) * 16 * motionScale;
  const sceneProgress = frame / Math.max(durationFrames, 1);
  const parallaxY = interpolate(sceneProgress, [0, 1], [18, -18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const horizontalBias = layout?.includes('left')
    ? -48
    : layout?.includes('right')
      ? 48
      : 0;
  const safeSubjectHeight = Math.min(SUBJECT_HEIGHT, CAPTION_SAFE_TOP - SUBJECT_TOP - 40);

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: SUBJECT_TOP,
          height: safeSubjectHeight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity,
          transform: `translate(${horizontalBias + driftX}px, ${enterY + floatY + parallaxY}px) scale(${enterScale})`,
          transformOrigin: 'center center',
        }}
      >
        {generatedAssetPath ? (
          <GeneratedAssetSubject
            theme={theme}
            generatedAssetPath={generatedAssetPath}
            frame={frame}
            motionScale={motionScale}
            width={width}
            height={height}
          />
        ) : (
          <VectorSubject
            kind={entityKind}
            theme={theme}
            frame={frame}
            motionScale={motionScale}
            width={width}
            height={height}
          />
        )}
        {imagePath && (
          <ImageReferenceCard
            theme={theme}
            imagePath={imagePath}
            frame={frame}
            motionScale={motionScale}
            width={width}
            height={height}
            side={layout?.includes('right') ? 'left' : 'right'}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

const GeneratedAssetSubject: React.FC<{
  theme: ThemeTokens;
  generatedAssetPath: string;
  frame: number;
  motionScale: number;
  width: number;
  height: number;
}> = ({theme, generatedAssetPath, frame, motionScale, width, height}) => {
  const stageWidth = Math.min(width - 112, 930);
  const stageHeight = Math.min(height * 0.41, 780);
  const glowX = 50 + Math.sin(frame / 70) * 18 * motionScale;
  const glowY = 48 + Math.cos(frame / 64) * 14 * motionScale;
  const tilt = Math.sin(frame / 72) * 0.85 * motionScale;
  const imageScale = 0.94 + Math.sin(frame / 96) * 0.012 * motionScale;

  return (
    <div
      style={{
        position: 'relative',
        width: stageWidth,
        height: stageHeight,
        borderRadius: 56,
        padding: 32,
        boxSizing: 'border-box',
        background: `linear-gradient(145deg, ${theme.surface}f2, ${theme.primary}22 48%, ${theme.secondary}2f), radial-gradient(circle at ${glowX}% ${glowY}%, ${theme.accent}44, transparent 46%)`,
        border: '2px solid rgba(255,255,255,0.2)',
        boxShadow: `0 52px 110px rgba(0,0,0,0.42), 0 0 78px ${theme.primary}3a, inset 0 0 0 1px rgba(255,255,255,0.08)`,
        transform: `perspective(1200px) rotateZ(${tilt}deg) rotateY(${tilt * 0.55}deg)`,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 18,
          borderRadius: 42,
          background: `linear-gradient(180deg, rgba(255,255,255,0.14), transparent 34%), radial-gradient(circle at 50% 72%, ${theme.caption_highlight}24, transparent 48%)`,
          boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.14)',
        }}
      />
      <Img
        src={staticFile(generatedAssetPath)}
        style={{
          position: 'relative',
          zIndex: 2,
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          filter: 'drop-shadow(0 30px 58px rgba(0,0,0,0.32))',
          transform: `scale(${imageScale})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(115deg, rgba(255,255,255,0.18), transparent 26%, transparent 72%, rgba(255,255,255,0.1))',
          mixBlendMode: 'screen',
        }}
      />
    </div>
  );
};

const ImageReferenceCard: React.FC<{
  theme: ThemeTokens;
  imagePath: string;
  frame: number;
  motionScale: number;
  width: number;
  height: number;
  side: 'left' | 'right';
}> = ({theme, imagePath, frame, motionScale, width, height, side}) => {
  const cardWidth = Math.min(width * 0.34, 360);
  const cardHeight = Math.min(height * 0.16, 260);
  const sheenX = ((frame * 5 * motionScale) % (cardWidth + 220)) - 180;
  const tilt = Math.sin(frame / 58) * 1.2 * motionScale;
  const slideX = interpolate(Math.min(frame, 18), [0, 18], [side === 'right' ? 120 : -120, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        [side]: Math.max(80, width * 0.08),
        bottom: 42,
        width: cardWidth,
        height: cardHeight,
        borderRadius: 30,
        padding: 10,
        background: `linear-gradient(145deg, ${theme.primary}55, ${theme.secondary}66 46%, ${theme.surface}ee)`,
        border: '2px solid rgba(255,255,255,0.18)',
        boxShadow: `0 24px 70px rgba(0,0,0,0.36), 0 0 60px ${theme.accent}22`,
        transform: `translateX(${slideX}px) perspective(900px) rotateZ(${tilt}deg) rotateY(${tilt * 0.65}deg)`,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at 20% 18%, ${theme.accent}55, transparent 34%), radial-gradient(circle at 86% 70%, ${theme.primary}44, transparent 38%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 26,
          left: 42,
          display: 'flex',
          gap: 10,
          zIndex: 2,
        }}
      >
        {[theme.primary, theme.accent, theme.caption_highlight].map((color, index) => (
          <div
            key={`${color}-${index}`}
            style={{
              width: 13,
              height: 13,
              borderRadius: 999,
              background: color,
              boxShadow: `0 0 18px ${color}`,
            }}
          />
        ))}
      </div>
      <div
        style={{
          position: 'absolute',
          top: 58,
          left: 20,
          right: 20,
          bottom: 20,
          borderRadius: 34,
          overflow: 'hidden',
          background: theme.surface,
          boxShadow: 'inset 0 0 0 2px rgba(255,255,255,0.12)',
        }}
      >
        <Img
          src={staticFile(imagePath)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${1.05 + Math.sin(frame / 80) * 0.018 * motionScale}) translate(${Math.sin(frame / 66) * -10 * motionScale}px, ${Math.cos(frame / 72) * -8 * motionScale}px)`,
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: sheenX,
          width: 160,
          transform: 'skewX(-18deg)',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent)',
        }}
      />
    </div>
  );
};


const VectorSubject: React.FC<EntityProps & {kind: SubjectEntityKind}> = ({kind, ...props}) => {
  if (kind === 'data_center') return <DataCenterEntity {...props} />;
  if (kind === 'city') return <CityEntity {...props} />;
  if (kind === 'power_grid') return <PowerGridEntity {...props} />;
  if (kind === 'chip') return <ChipEntity {...props} />;
  if (kind === 'globe_network') return <GlobeNetworkEntity {...props} />;
  return <GenericExplainerEntity {...props} />;
};

const EntityStage: React.FC<EntityProps & {children: React.ReactNode}> = ({
  theme,
  frame,
  motionScale,
  width,
  height,
  children,
}) => {
  const stageWidth = Math.min(width - 92, 940);
  const stageHeight = Math.min(height * 0.44, 820);
  const rotate = Math.sin(frame / 64) * 1.1 * motionScale;

  return (
    <svg
      width={stageWidth}
      height={stageHeight}
      viewBox="0 0 940 820"
      role="img"
      aria-label="Animated scene subject"
      style={{
        overflow: 'visible',
        filter: `drop-shadow(0 42px 80px rgba(0,0,0,0.38)) drop-shadow(0 0 46px ${theme.primary}33)`,
        transform: `rotate(${rotate}deg)`,
      }}
    >
      <defs>
        <linearGradient id="subject-body" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={theme.primary} />
          <stop offset="0.55" stopColor={theme.secondary} />
          <stop offset="1" stopColor={theme.accent} />
        </linearGradient>
        <linearGradient id="subject-glow" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={theme.caption_highlight} stopOpacity="0" />
          <stop offset="0.5" stopColor={theme.caption_highlight} stopOpacity="0.85" />
          <stop offset="1" stopColor={theme.caption_highlight} stopOpacity="0" />
        </linearGradient>
        <filter id="soft-glow">
          <feGaussianBlur stdDeviation="9" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <ellipse cx="470" cy="705" rx="325" ry="46" fill="#000000" opacity="0.24" />
      {children}
    </svg>
  );
};

const DataCenterEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  const flowOffset = (frame * 8 * motionScale) % 240;

  return (
    <EntityStage {...props}>
      <rect x="90" y="135" width="760" height="510" rx="42" fill={theme.surface} opacity="0.86" />
      <rect x="116" y="164" width="708" height="454" rx="30" fill="url(#subject-body)" opacity="0.18" />
      {RACK_X.map((x, rackIndex) => (
        <g key={x} transform={`translate(${x} 205)`}>
          <rect width="134" height="382" rx="24" fill={theme.secondary} stroke="rgba(255,255,255,0.2)" strokeWidth="4" />
          {LIGHT_PHASES.map((phase, row) => {
            const glow = 0.45 + Math.max(0, Math.sin(frame / 6 + phase + rackIndex)) * 0.55;
            return (
              <g key={phase} transform={`translate(18 ${30 + row * 66})`}>
                <rect width="98" height="36" rx="12" fill="#ffffff" opacity="0.08" />
                <circle cx="22" cy="18" r="7" fill={theme.caption_highlight} opacity={glow} filter="url(#soft-glow)" />
                <rect x="42" y="13" width="50" height="10" rx="5" fill={theme.accent} opacity={0.25 + glow * 0.5} />
              </g>
            );
          })}
        </g>
      ))}
      {[0, 1, 2].map((line) => (
        <g key={line} opacity="0.82">
          <path
            d={`M160 ${250 + line * 95} C310 ${180 + line * 45}, 570 ${350 - line * 34}, 792 ${245 + line * 88}`}
            fill="none"
            stroke="rgba(255,255,255,0.18)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <rect
            x={(flowOffset + line * 84) % 710 + 115}
            y={238 + line * 93 + Math.sin(frame / 9 + line) * 16}
            width="86"
            height="12"
            rx="6"
            fill="url(#subject-glow)"
            filter="url(#soft-glow)"
          />
        </g>
      ))}
      <g transform={`translate(640 ${92 + Math.sin(frame / 18) * 9 * motionScale})`}>
        <path
          d="M58 92h145c43 0 78-30 78-69 0-37-32-67-73-67-17-46-63-76-116-76-65 0-118 46-123 104-44 7-77 40-77 80 0 45 40 81 108 81z"
          fill={theme.accent}
          opacity="0.88"
        />
        <path d="M1 82h262" stroke="#fff" strokeWidth="10" strokeLinecap="round" opacity="0.28" />
      </g>
    </EntityStage>
  );
};

const CityEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  return (
    <EntityStage {...props}>
      <circle cx="724" cy="154" r="88" fill={theme.accent} opacity="0.88" filter="url(#soft-glow)" />
      <path d="M70 612h800" stroke="rgba(255,255,255,0.28)" strokeWidth="18" strokeLinecap="round" />
      {CITY_BUILDINGS.map((building, buildingIndex) => {
        const fill = building.tone === 0 ? theme.secondary : building.tone === 1 ? theme.primary : theme.surface;
        return (
          <g key={building.x}>
            <rect
              x={building.x}
              y={building.y + Math.sin(frame / 36 + buildingIndex) * 4 * motionScale}
              width={building.w}
              height={building.h}
              rx="22"
              fill={fill}
              stroke="rgba(255,255,255,0.18)"
              strokeWidth="4"
            />
            {[0, 1, 2].map((col) =>
              [0, 1, 2, 3].map((row) => {
                const blink = 0.25 + Math.max(0, Math.sin(frame / 8 + row + col + buildingIndex)) * 0.55;
                return (
                  <rect
                    key={`${col}-${row}`}
                    x={building.x + 24 + col * 30}
                    y={building.y + 36 + row * 50}
                    width="16"
                    height="22"
                    rx="5"
                    fill={theme.accent}
                    opacity={blink}
                  />
                );
              }),
            )}
          </g>
        );
      })}
      <path
        d={`M122 ${498 + Math.sin(frame / 20) * 8 * motionScale} C252 420, 334 438, 458 366 S662 284, 804 314`}
        fill="none"
        stroke={theme.caption_highlight}
        strokeWidth="12"
        strokeLinecap="round"
        opacity="0.76"
        filter="url(#soft-glow)"
      />
      <g transform={`translate(${136 + Math.sin(frame / 24) * 14 * motionScale} 178)`}>
        <rect x="0" y="0" width="168" height="104" rx="24" fill="#ffffff" opacity="0.14" />
        <path d="M36 68h96M36 40h70" stroke="#fff" strokeWidth="12" strokeLinecap="round" opacity="0.62" />
      </g>
    </EntityStage>
  );
};

const PowerGridEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  const pulse = (frame * 9 * motionScale) % 640;

  return (
    <EntityStage {...props}>
      <path d="M130 274 C332 170, 590 174, 812 276" fill="none" stroke="rgba(255,255,255,0.24)" strokeWidth="9" />
      <path d="M130 348 C342 250, 596 248, 812 348" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="9" />
      <circle cx={150 + pulse} cy={270 + Math.sin(frame / 10) * 18} r="16" fill={theme.caption_highlight} opacity="0.85" filter="url(#soft-glow)" />
      <circle cx={140 + ((pulse + 260) % 640)} cy={346 + Math.cos(frame / 10) * 14} r="12" fill={theme.accent} opacity="0.86" filter="url(#soft-glow)" />
      <Pylon x={120} y={236} scale={1.05} color={theme.secondary} accent={theme.primary} />
      <Pylon x={390} y={178} scale={1.28} color={theme.primary} accent={theme.accent} />
      <Pylon x={704} y={246} scale={1.02} color={theme.secondary} accent={theme.caption_highlight} />
      <g transform={`translate(404 ${430 + Math.sin(frame / 16) * 12 * motionScale})`}>
        <path d="M112 0 36 134h78l-34 132 128-178h-82l48-88z" fill={theme.accent} filter="url(#soft-glow)" />
        <path d="M112 0 36 134h78" fill="none" stroke="#fff" strokeWidth="10" opacity="0.34" />
      </g>
    </EntityStage>
  );
};

const Pylon: React.FC<{x: number; y: number; scale: number; color: string; accent: string}> = ({x, y, scale, color, accent}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M90 0 20 340h140L90 0z" fill={color} opacity="0.94" />
    <path d="M90 34 50 132h80L90 34zM45 164h90M35 214h110M25 266h130" stroke="#fff" strokeWidth="8" opacity="0.25" />
    <path d="M-24 94h228M-10 138h200" stroke={accent} strokeWidth="12" strokeLinecap="round" />
    <circle cx="90" cy="44" r="15" fill={accent} filter="url(#soft-glow)" />
  </g>
);

const ChipEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  const scan = 166 + ((frame * 5 * motionScale) % 268);

  return (
    <EntityStage {...props}>
      <g transform={`translate(230 ${130 + Math.sin(frame / 28) * 8 * motionScale})`}>
        {CHIP_PINS.map((pin) => (
          <React.Fragment key={pin}>
            <rect x={-56} y={86 + pin * 48} width="72" height="18" rx="9" fill={theme.accent} opacity="0.82" />
            <rect x={454} y={86 + pin * 48} width="72" height="18" rx="9" fill={theme.accent} opacity="0.82" />
            <rect x={86 + pin * 48} y={-56} width="18" height="72" rx="9" fill={theme.accent} opacity="0.82" />
            <rect x={86 + pin * 48} y={454} width="18" height="72" rx="9" fill={theme.accent} opacity="0.82" />
          </React.Fragment>
        ))}
        <rect width="470" height="470" rx="66" fill={theme.secondary} stroke={theme.primary} strokeWidth="10" />
        <rect x="70" y="70" width="330" height="330" rx="44" fill={theme.surface} stroke="rgba(255,255,255,0.18)" strokeWidth="5" />
        <path d="M126 264h218M236 126v218M150 166h74v74h94v78" stroke={theme.caption_highlight} strokeWidth="16" strokeLinecap="round" strokeLinejoin="round" opacity="0.88" />
        <rect x="88" y={scan} width="294" height="22" rx="11" fill="url(#subject-glow)" filter="url(#soft-glow)" />
        {[0, 1, 2, 3].map((node) => (
          <circle
            key={node}
            cx={142 + node * 66}
            cy={166 + ((node % 2) * 150)}
            r={18 + Math.max(0, Math.sin(frame / 7 + node)) * 6}
            fill={node % 2 === 0 ? theme.accent : theme.primary}
            filter="url(#soft-glow)"
          />
        ))}
      </g>
      <g opacity="0.46">
        <path d="M116 624C248 552 334 642 470 562s246-10 354-82" fill="none" stroke="#fff" strokeWidth="10" strokeLinecap="round" />
        <path d="M148 668h646" stroke="rgba(255,255,255,0.2)" strokeWidth="16" strokeLinecap="round" />
      </g>
    </EntityStage>
  );
};

const GlobeNetworkEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  const spin = frame * 1.7 * motionScale;

  return (
    <EntityStage {...props}>
      <g transform={`translate(470 ${390 + Math.sin(frame / 28) * 10 * motionScale})`}>
        <circle r="230" fill={theme.secondary} stroke={theme.primary} strokeWidth="10" />
        <circle r="205" fill="url(#subject-body)" opacity="0.18" />
        <ellipse rx="206" ry="74" fill="none" stroke="rgba(255,255,255,0.28)" strokeWidth="8" />
        <ellipse rx="88" ry="205" fill="none" stroke="rgba(255,255,255,0.28)" strokeWidth="8" />
        <path d="M-172-96C-66-24 44-20 178-98M-178 98C-54 24 66 22 174 96" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="8" />
        <path d="M-150 44C-58-76 78-86 156 38" fill="none" stroke={theme.caption_highlight} strokeWidth="13" strokeLinecap="round" filter="url(#soft-glow)" />
        {ORBIT_NODES.map((node) => {
          const angle = (spin + node * 60) * (Math.PI / 180);
          const x = Math.cos(angle) * 274;
          const y = Math.sin(angle) * 118;
          return (
            <g key={node} transform={`translate(${x} ${y})`}>
              <circle r="20" fill={node % 2 === 0 ? theme.accent : theme.caption_highlight} filter="url(#soft-glow)" />
              <circle r="38" fill="none" stroke="#fff" strokeWidth="4" opacity="0.22" />
            </g>
          );
        })}
      </g>
      <path d="M160 208C282 74 658 70 790 212" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="10" strokeLinecap="round" />
      <path d="M154 574C330 700 640 700 806 568" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="10" strokeLinecap="round" />
    </EntityStage>
  );
};

const GenericExplainerEntity: React.FC<EntityProps> = (props) => {
  const {theme, frame, motionScale} = props;
  const orb = frame * 2.2 * motionScale;

  return (
    <EntityStage {...props}>
      <g transform={`translate(470 ${392 + Math.sin(frame / 26) * 12 * motionScale})`}>
        <rect x="-228" y="-196" width="456" height="392" rx="64" fill={theme.secondary} stroke="rgba(255,255,255,0.2)" strokeWidth="6" />
        <circle cx="-92" cy="-56" r="88" fill={theme.primary} opacity="0.9" />
        <rect x="30" y="-128" width="142" height="142" rx="34" fill={theme.accent} opacity="0.9" />
        <path d="M-146 110h292M-102 150h204" stroke="#fff" strokeWidth="18" strokeLinecap="round" opacity="0.38" />
        <path d="M-92-56C-16-126 74-106 102-58S126 50 30 86" fill="none" stroke={theme.caption_highlight} strokeWidth="13" strokeLinecap="round" filter="url(#soft-glow)" />
        {[0, 1, 2].map((node) => {
          const angle = (orb + node * 120) * (Math.PI / 180);
          return (
            <circle
              key={node}
              cx={Math.cos(angle) * 318}
              cy={Math.sin(angle) * 162}
              r="24"
              fill={node === 0 ? theme.accent : node === 1 ? theme.primary : theme.caption_highlight}
              filter="url(#soft-glow)"
            />
          );
        })}
      </g>
    </EntityStage>
  );
};
