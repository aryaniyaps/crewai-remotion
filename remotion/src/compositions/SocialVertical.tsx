import React from 'react';
import {AbsoluteFill, Audio, staticFile, useVideoConfig} from 'remotion';
import {TransitionSeries} from '@remotion/transitions';
import type {VideoSpecProps} from '../schema';
import {BeatScene} from '../scenes/BeatScene';
import {BackgroundLayer} from '../layers/BackgroundLayer';
import {CaptionLayer} from '../layers/CaptionLayer';
import {SFXLayer} from '../layers/SFXLayer';
import {resolveCut} from '../design/cuts';
import type {CutType} from '../design/cuts';

/**
 * SocialVertical — 1080×1920 composition.
 *
 * Renders beats through TransitionSeries with agent-chosen cut types.
 * Audio (VO + music + SFX) is continuous; captions overlay the full timeline.
 * Motion graphics, parallax depth, and camera motion are per-beat.
 * Duration comes from audio.duration_sec via calculateMetadata.
 */
export const SocialVertical: React.FC<VideoSpecProps> = (props) => {
  const {scenes, theme, captions, audio, edit_decisions} = props;
  const {fps} = useVideoConfig();

  // Build flat word list from caption segments for CaptionLayer
  const allWords = (captions ?? []).flatMap(
    (seg: {words?: {text: string; start_ms: number; end_ms: number}[]}) =>
      seg.words ?? [],
  );

  // SFX cues from props
  const sfxCues = audio?.sfx?.cues ?? [];

  // Voiceover path (relative to public/ or absolute)
  const voPath = audio?.voiceover as string | undefined;
  const musicPath = audio?.music_path as string | undefined;
  const musicVolume = (audio?.music_volume as number) ?? 0.25;
  const durationSec = (audio?.duration_sec as number) ?? 30;
  const hasCaptions = allWords.length > 0;

  // Build beat sequence for TransitionSeries
  const beats = scenes.map((scene, i) => {
    // Determine cut type for transition INTO this beat
    const cutType: CutType =
      i === 0
        ? 'j_cut' // First beat: J-cut in from black
        : (scene.cut_type as CutType) ?? 'hard_cut';

    const cut = resolveCut(cutType, (theme.motion_style as 'snappy' | 'smooth' | 'kinetic') ?? 'snappy');

    return {
      scene,
      cut,
      cutType,
      // J-cut: audio leads — sequence starts early, transition is 1 frame
      // L-cut: audio trails — handled by next beat's offset
    };
  });

  return (
    <AbsoluteFill style={{backgroundColor: theme.surface}}>
      {/* Continuous background */}
      <BackgroundLayer theme={theme} />

      {/* SFX layer — independent audio cues, above background */}
      <SFXLayer cues={sfxCues} />

      <TransitionSeries>
        {beats.map(({scene, cut}, i) => (
          <React.Fragment key={scene.id}>
            {/* Transition into this beat (skip first beat's entry transition) */}
            {i > 0 && (
              <TransitionSeries.Transition
                presentation={cut.presentation}
                timing={cut.timing}
              />
            )}

            {/* Beat sequence */}
            <TransitionSeries.Sequence
              durationInFrames={scene.duration_frames}
            >
              <BeatScene
                theme={theme}
                headline={scene.headline}
                subhead={scene.subhead}
                sceneType={scene.type}
                backgroundVariant={scene.background_variant}
                layout={scene.layout}
                imagePath={scene.image_path}
                generatedAssetPath={scene.generated_asset_path}
                animatedAssetPath={scene.animated_asset_path}
                animatedAssetType={scene.animated_asset_type}
                illustrationId={scene.illustration_id}
                showHeadline={!hasCaptions}
                motionGraphics={scene.motion_graphics}
                motionIntent={scene.motion_intent}
                motionIntensity={scene.motion_intensity ?? 'medium'}
                parallaxDepth={scene.parallax_depth ?? 0}
                cameraMotion={scene.camera_motion}
                durationFrames={scene.duration_frames}
              />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
      </TransitionSeries>

      {/* Voiceover — continuous audio layer, not per-sequence */}
      {voPath && <Audio src={staticFile(voPath)} volume={1} />}

      {/* Background music — ducked under VO */}
      {musicPath && <Audio src={staticFile(musicPath)} volume={musicVolume} />}

      {/* Captions overlay — follows Whisper word timestamps */}
      <CaptionLayer
        theme={theme}
        words={allWords}
      />
    </AbsoluteFill>
  );
};
