import type {TransitionPresentation} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import {linearTiming, springTiming, TransitionTiming} from '@remotion/transitions';

export type CutType =
  | 'hard_cut'
  | 'jump_cut'
  | 'match_cut'
  | 'smash_cut'
  | 'cut_on_action'
  | 'j_cut'
  | 'l_cut'
  | 'cross_cut'
  | 'montage'
  | 'dissolve'
  | 'invisible_cut';

export type SplitEdit = 'none' | 'j_cut' | 'l_cut';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyPresentation = TransitionPresentation<any>;

export interface CutResult {
  presentation: AnyPresentation;
  timing: TransitionTiming;
  durationFrames: number;
  /** Whether an overlay flash/impact is needed (smash_cut) */
  overlay: boolean;
  overlayDurationFrames?: number;
  cutOnActionFraction?: number;
}

/**
 * Map agent-chosen cut_type → Remotion TransitionSeries primitives.
 */
export const resolveCut = (
  cutType: CutType,
  motionStyle: 'snappy' | 'smooth' | 'kinetic' = 'snappy',
): CutResult => {
  switch (cutType) {
    case 'hard_cut':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 3}),
        durationFrames: 3,
        overlay: false,
      };

    case 'jump_cut':
      return {
        presentation: slide({direction: 'from-bottom'}),
        timing: springTiming({config: {damping: 20, stiffness: 200}}),
        durationFrames: 6,
        overlay: false,
      };

    case 'match_cut':
      return {
        presentation: slide({direction: 'from-right'}),
        timing: springTiming({config: {damping: 30, stiffness: 120}}),
        durationFrames: 8,
        overlay: false,
      };

    case 'smash_cut':
      return {
        presentation: wipe(),
        timing: linearTiming({durationInFrames: 6}),
        durationFrames: 6,
        overlay: true,
        overlayDurationFrames: 8,
      };

    case 'cut_on_action':
      return {
        presentation: slide({direction: 'from-bottom'}),
        timing: springTiming({config: {damping: 20, stiffness: 200}}),
        durationFrames: 4,
        overlay: false,
        cutOnActionFraction: 0.7,
      };

    case 'j_cut':
    case 'l_cut':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 1}),
        durationFrames: 1,
        overlay: false,
      };

    case 'cross_cut':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 3}),
        durationFrames: 3,
        overlay: false,
      };

    case 'montage':
      return {
        presentation: slide({direction: 'from-right'}),
        timing: linearTiming({durationInFrames: 4}),
        durationFrames: 4,
        overlay: false,
      };

    case 'dissolve':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 14}),
        durationFrames: 14,
        overlay: false,
      };

    case 'invisible_cut':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 1}),
        durationFrames: 1,
        overlay: false,
      };

    default:
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 3}),
        durationFrames: 3,
        overlay: false,
      };
  }
};

export const DEFAULT_CUT_RHYTHM: Array<{from: string; to: string; cut: CutType}> = [
  {from: 'start', to: 'hook', cut: 'j_cut'},
  {from: 'hook', to: 'body_1', cut: 'hard_cut'},
  {from: 'body_1', to: 'body_2', cut: 'match_cut'},
  {from: 'body_2', to: 'body_3', cut: 'hard_cut'},
  {from: 'body_3', to: 'cta', cut: 'l_cut'},
];

export const SFX_BRIDGE: Record<CutType, string | null> = {
  hard_cut: null,
  jump_cut: 'whoosh',
  match_cut: 'whoosh_low',
  smash_cut: 'impact',
  cut_on_action: 'swoosh',
  j_cut: null,
  l_cut: null,
  cross_cut: 'whoosh',
  montage: 'whoosh_low',
  dissolve: null,
  invisible_cut: null,
};

export const MAX_SMASH_CUTS_PER_30S = 1;

export const J_CUT_LEAD_RANGE = {min: 3, max: 8} as const;

export const L_CUT_TRAIL_RANGE = {min: 6, max: 15} as const;
