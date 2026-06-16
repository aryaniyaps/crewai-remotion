import {z} from 'zod';
import {zColor} from '@remotion/zod-types';

// ── Scene ──

export const SceneSchema = z.object({
  id: z.string(),
  type: z.enum(['HookBeat', 'PointBeat', 'StatBeat', 'QuoteBeat', 'CTABeat']),
  headline: z.string(),
  subhead: z.string().optional(),
  duration_frames: z.number().int().positive(),
  illustration_id: z.string().nullable().optional(),
  image_path: z.string().nullable().optional(),
  background_variant: z.enum(['primary', 'secondary', 'surface']).optional(),
  layout: z
    .enum([
      'left_stack',
      'right_stack',
      'center_focus',
      'top_down',
      'diagonal_tl_br',
      'diagonal_tr_bl',
    ])
    .optional(),
  motion_intent: z
    .enum(['enter_up', 'fade_in', 'scale_burst', 'slide_in'])
    .optional(),
  cut_type: z
    .enum([
      'hard_cut',
      'jump_cut',
      'match_cut',
      'smash_cut',
      'cut_on_action',
      'j_cut',
      'l_cut',
      'cross_cut',
      'montage',
      'dissolve',
      'invisible_cut',
    ])
    .optional(),
  motion_graphics: z
    .array(
      z.object({
        id: z.string(),
        type: z.enum([
          'particles',
          'wave',
          'ring_pulse',
          'geometric_morph',
          'data_flow',
          'energy_burst',
          'orbital',
          'text_shatter',
          'grid_pulse',
          'glow_trail',
          'kinetic_type_zoom',
        ]),
        config: z.record(z.unknown()).optional(),
        entry_frame: z.number().int().optional(),
        exit_frame: z.number().int().optional(),
      }),
    )
    .optional(),
  motion_intensity: z.enum(['low', 'medium', 'high']).optional(),
  parallax_depth: z.number().min(0).max(1).optional(),
  camera_motion: z
    .enum([
      'none',
      'push_in',
      'pull_out',
      'pan_left',
      'pan_right',
      'tilt_up',
      'tilt_down',
      'handheld',
    ])
    .optional(),
});

// ── Theme ──

export const ThemeSchema = z.object({
  primary: zColor(),
  secondary: zColor(),
  accent: zColor(),
  surface: zColor(),
  caption_highlight: zColor(),
  font_heading: z.string(),
  font_body: z.string(),
  motion_style: z.enum(['snappy', 'smooth', 'kinetic']),
  texture: z.enum(['none', 'grain', 'paper']),
});

// ── Captions ──

export const CaptionWordSchema = z.object({
  text: z.string(),
  start_ms: z.number(),
  end_ms: z.number(),
});

export const CaptionSegmentSchema = z.object({
  words: z.array(CaptionWordSchema),
});

// ── Edit Decisions ──

export const EditDecisionSchema = z.object({
  scene_id: z.string(),
  cut_type: z
    .enum([
      'hard_cut',
      'jump_cut',
      'match_cut',
      'smash_cut',
      'cut_on_action',
      'j_cut',
      'l_cut',
      'cross_cut',
      'montage',
      'dissolve',
      'invisible_cut',
    ])
    .optional(),
  split_edit: z.enum(['none', 'j_cut', 'l_cut']).optional(),
  audio_sync_ref: z.string().optional(),
  offset_frames: z.number().optional(),
  notes: z.string().optional(),
});

export const EditDecisionListSchema = z.object({
  decisions: z.array(EditDecisionSchema),
  pacing_notes: z.string().optional(),
});

// ── VideoSpec (top-level) ──

export const VideoSpecSchema = z.object({
  title: z.string(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  fps: z.number().int().positive(),
  duration_frames: z.number().int().positive(),
  theme: ThemeSchema,
  scenes: z.array(SceneSchema),
  captions: z.array(CaptionSegmentSchema).optional(),
  edit_decisions: EditDecisionListSchema.optional(),
  audio: z
    .object({
      voiceover: z.string().optional(),
      music_path: z.string().optional(),
      music_volume: z.number().min(0).max(1).optional(),
      duration_sec: z.number().positive().optional(),
      sfx: z
        .object({
          cues: z.array(
            z.object({
              frame: z.number().int(),
              src: z.string(),
              volume: z.number().optional(),
              cut_type: z.string().optional(),
            }),
          ),
        })
        .optional(),
    })
    .optional(),
});

export type VideoSpecProps = z.infer<typeof VideoSpecSchema>;
export type SceneSpec = z.infer<typeof SceneSchema>;
export type ThemeTokens = z.infer<typeof ThemeSchema>;
