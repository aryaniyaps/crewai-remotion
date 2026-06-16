import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';

/**
 * A single timed sound effect cue.
 */
export interface SfxCue {
  /** Frame number in the composition where this SFX fires. */
  frame: number;
  /** Local public path, usually `runs/<id>/<file>`. Remote URLs are ignored. */
  src: string;
  /** Playback volume 0–1. Defaults to 0.7. */
  volume?: number;
  /** The cut type this SFX accompanies, for debugging. */
  cut_type?: string;
}

export interface SFXLayerProps {
  cues: SfxCue[];
}

type CueKind = 'impact' | 'whoosh' | 'crisp' | 'neutral';

const clampVolume = (volume: number): number => {
  if (!Number.isFinite(volume)) return 0.7;
  return Math.min(1, Math.max(0, volume));
};

const getCueKind = (cue: SfxCue): CueKind => {
  const source = cue.src.toLowerCase();
  const cutType = (cue.cut_type ?? '').toLowerCase();

  if (source.includes('pop') || source.includes('click')) {
    return 'crisp';
  }
  if (
    source.includes('whoosh') ||
    source.includes('swoosh') ||
    source.includes('swish') ||
    source.includes('sweep') ||
    source.includes('rise') ||
    source.includes('transition')
  ) {
    return 'whoosh';
  }
  if (
    source.includes('impact') ||
    source.includes('bass_hit') ||
    source.includes('bass-hit') ||
    source.includes('hit')
  ) {
    return 'impact';
  }
  if (
    cutType.includes('jump_cut') ||
    cutType.includes('cross_cut') ||
    cutType.includes('match_cut') ||
    cutType.includes('montage') ||
    cutType.includes('cut_on_action')
  ) {
    return 'whoosh';
  }
  if (cutType.includes('smash') || cutType.includes('reveal')) {
    return 'impact';
  }
  return 'neutral';
};

const getTimingOffset = (kind: CueKind): number => {
  if (kind === 'whoosh') return -3;
  if (kind === 'crisp') return 1;
  return 0;
};

const shapeVolume = (cue: SfxCue, kind: CueKind): number => {
  const base = clampVolume(cue.volume ?? 0.7);
  if (kind === 'impact') return clampVolume(base * 1.15);
  if (kind === 'whoosh') return clampVolume(base * 0.82);
  if (kind === 'crisp') return base === 0 ? 0 : clampVolume(base * 0.95 + 0.05);
  return base;
};

const envelopeFor = (kind: CueKind): {fadeIn: number; fullUntil: number; fadeOut: number} => {
  if (kind === 'crisp') return {fadeIn: 0, fullUntil: 7, fadeOut: 3};
  if (kind === 'impact') return {fadeIn: 0, fullUntil: 16, fadeOut: 5};
  if (kind === 'whoosh') return {fadeIn: 2, fullUntil: 24, fadeOut: 6};
  return {fadeIn: 1, fullUntil: 18, fadeOut: 5};
};

const makeVolumeEnvelope = (
  shapedVolume: number,
  kind: CueKind,
): ((frame: number) => number) => {
  const {fadeIn, fullUntil, fadeOut} = envelopeFor(kind);
  return (frame: number) => {
    const safeFrame = Math.max(0, frame);
    let envelope = 1;
    if (fadeIn > 0 && safeFrame < fadeIn) {
      envelope = safeFrame / fadeIn;
    } else if (safeFrame > fullUntil) {
      envelope = Math.max(0, 1 - (safeFrame - fullUntil) / fadeOut);
    }
    return clampVolume(shapedVolume * envelope);
  };
};

const isUnsupportedStaticSrc = (src: string): boolean =>
  src.startsWith('http://') ||
  src.startsWith('https://') ||
  src.startsWith('..') ||
  src.startsWith('./') ||
  src.startsWith('public/') ||
  src.startsWith('/Users') ||
  src.startsWith('/home') ||
  src.startsWith('/tmp') ||
  src.startsWith('/etc') ||
  src.startsWith('/opt') ||
  src.startsWith('/var') ||
  /^[A-Z]:/.test(src);

/**
 * Plays timed sound effects at specific frames.
 *
 * Each cue is wrapped in a `<Sequence>` so it renders only at its shaped trigger
 * frame. Local paths go through `staticFile()`; remote URLs are intentionally
 * ignored so renders do not depend on CDN/CORS behavior.
 */
export const SFXLayer: React.FC<SFXLayerProps> = ({cues}) => {
  if (!cues || cues.length === 0) return null;

  return (
    <>
      {cues.map((cue, i) => {
        // Only call staticFile() for paths Remotion accepts from public/.
        if (!cue.src || isUnsupportedStaticSrc(cue.src)) return null;
        try {
          const src = staticFile(cue.src);
          const kind = getCueKind(cue);
          const cueFrame = Number.isFinite(cue.frame) ? cue.frame : 0;
          const from = Math.max(0, Math.round(cueFrame + getTimingOffset(kind)));
          const volume = makeVolumeEnvelope(shapeVolume(cue, kind), kind);

          return (
            <Sequence key={`sfx-${i}-${from}`} from={from}>
              <Audio src={src} volume={volume} />
            </Sequence>
          );
        } catch {
          // staticFile throws on invalid paths — skip gracefully.
          return null;
        }
      })}
    </>
  );
};
