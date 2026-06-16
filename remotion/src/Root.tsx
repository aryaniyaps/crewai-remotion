import React from 'react';
import {loadFont} from '@remotion/google-fonts/SpaceGrotesk';
import {Composition} from 'remotion';
import type {CalculateMetadataFunction} from 'remotion';
import {SocialVertical} from './compositions/SocialVertical';
import {VideoSpecSchema, type VideoSpecProps} from './schema';
import {defaultTheme} from './design/tokens';

loadFont('normal', {weights: ['400','500','700']});

const defaultProps: VideoSpecProps = {
  title: 'Preview',
  width: 1080,
  height: 1920,
  fps: 30,
  duration_frames: 300,
  theme: defaultTheme,
  scenes: [
    {
      id: 'b0',
      type: 'HookBeat',
      headline: 'Stop scrolling',
      subhead: 'This changes everything',
      duration_frames: 90,
      cut_type: 'j_cut',
    },
    {
      id: 'b1',
      type: 'PointBeat',
      headline: 'Ship faster',
      subhead: 'With the right stack',
      duration_frames: 120,
      cut_type: 'hard_cut',
    },
    {
      id: 'b2',
      type: 'CTABeat',
      headline: 'Follow for more',
      duration_frames: 90,
      cut_type: 'l_cut',
    },
  ],
  captions: [],
  audio: {},
  edit_decisions: {
    decisions: [],
    pacing_notes: '',
  },
};

/**
 * calculateMetadata: duration follows audio length, not a hardcoded frame count.
 * If audio.duration_sec is present, override durationInFrames.
 */
const calculateMetadata: CalculateMetadataFunction<VideoSpecProps> = async ({
  props,
}) => {
  const audioDuration = props.audio?.duration_sec as number | undefined;
  if (audioDuration && audioDuration > 0) {
    const fps = props.fps ?? 30;
    const durationInFrames = Math.ceil(audioDuration * fps);
    return {
      durationInFrames,
      props,
    };
  }
  // Fall back to sum of scene durations
  const totalFrames = (props.scenes ?? []).reduce(
    (sum, s) => sum + (s.duration_frames ?? 90),
    0,
  );
  return {
    durationInFrames: totalFrames > 0 ? totalFrames : props.duration_frames,
    props,
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SocialVertical"
        component={SocialVertical}
        durationInFrames={defaultProps.duration_frames}
        fps={defaultProps.fps}
        width={defaultProps.width}
        height={defaultProps.height}
        defaultProps={defaultProps}
        schema={VideoSpecSchema}
        calculateMetadata={calculateMetadata}
      />
    </>
  );
};
