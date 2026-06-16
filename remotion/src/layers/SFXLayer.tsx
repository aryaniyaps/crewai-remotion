import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';

/**
 * A single timed sound effect cue.
 */
export interface SfxCue {
  /** Frame number in the composition where this SFX fires. */
  frame: number;
  /** Source path — either a `runs/<id>/` relative path for local files
   *  or a full URL for CDN-hosted sounds. */
  src: string;
  /** Playback volume 0–1. Defaults to 0.7. */
  volume?: number;
  /** The cut type this SFX accompanies, for debugging. */
  cut_type?: string;
}

export interface SFXLayerProps {
  cues: SfxCue[];
}

/**
 * Plays timed sound effects at specific frames.
 *
 * Each cue is wrapped in a `<Sequence>` so it renders only at its trigger
 * frame. The underlying `<Audio>` plays once when its sequence becomes
 * active — we rely on browser-native audio to play the full sample;
 * one-shot short SFX (< 2 s) don't need explicit trimming.
 *
 * CDN URLs are passed directly; local paths go through `staticFile()`.
 */
export const SFXLayer: React.FC<SFXLayerProps> = ({cues}) => {
  if (!cues || cues.length === 0) return null;

  return (
    <>
      {cues.map((cue, i) => {
        // Only handle http(s) URLs or local paths — skip empty/broken src
        if (!cue.src) return null;
        try {
          const src = cue.src.startsWith('http')
            ? cue.src
            : staticFile(cue.src);
          const volume = cue.volume ?? 0.7;

          return (
            <Sequence key={`sfx-${i}-${cue.frame}`} from={cue.frame}>
              <Audio src={src} volume={volume} />
            </Sequence>
          );
        } catch {
          // staticFile throws on missing files — skip gracefully
          return null;
        }
      })}
    </>
  );
};
