export type MotionGraphicType =
  | 'particles'
  | 'wave'
  | 'ring_pulse'
  | 'geometric_morph'
  | 'data_flow'
  | 'energy_burst'
  | 'orbital'
  | 'text_shatter'
  | 'grid_pulse'
  | 'glow_trail'
  | 'kinetic_type_zoom';

export interface MotionGraphic {
  id: string;
  type: MotionGraphicType;
  config?: Record<string, unknown>;
  entry_frame?: number;
  exit_frame?: number;
}

export interface MotionGraphicTemplate {
  id: string;
  type: MotionGraphicType;
  label: string;
  description: string;
  defaultConfig: Record<string, unknown>;
  intensity: 'low' | 'medium' | 'high';
  tags: string[];
}

export const MOTION_GRAPHIC_CATALOG: MotionGraphicTemplate[] = [
  {
    id: 'ambient_dust',
    type: 'particles',
    label: 'Ambient Dust',
    description: 'Slow-floating particle field for subtle atmosphere',
    defaultConfig: {count: 40, speed: 0.3, spread: 300, color: 'theme', size: 3},
    intensity: 'low',
    tags: ['ambient', 'subtle', 'atmosphere'],
  },
  {
    id: 'energy_sparks',
    type: 'particles',
    label: 'Energy Sparks',
    description: 'Fast-moving bright sparks for high-energy moments',
    defaultConfig: {count: 60, speed: 1.2, spread: 400, color: 'accent', size: 5},
    intensity: 'high',
    tags: ['energy', 'spark', 'dynamic'],
  },
  {
    id: 'gentle_wave',
    type: 'wave',
    label: 'Gentle Wave',
    description: 'Calm sine wave for smooth transitions',
    defaultConfig: {amplitude: 20, frequency: 0.5, phase: 0, layers: 2, color: 'primary'},
    intensity: 'low',
    tags: ['calm', 'organic', 'flow'],
  },
  {
    id: 'aggressive_wave',
    type: 'wave',
    label: 'Aggressive Wave',
    description: 'High-amplitude rapid wave for energetic beats',
    defaultConfig: {amplitude: 50, frequency: 2, phase: 0, layers: 4, color: 'accent'},
    intensity: 'high',
    tags: ['energy', 'dynamic', 'impact'],
  },
  {
    id: 'sonar_scan',
    type: 'ring_pulse',
    label: 'Sonar Scan',
    description: 'Expanding concentric rings like radar/sonar',
    defaultConfig: {count: 4, maxRadius: 300, interval: 15, color: 'accent'},
    intensity: 'medium',
    tags: ['tech', 'radar', 'pulse'],
  },
  {
    id: 'ripple_center',
    type: 'ring_pulse',
    label: 'Ripple Center',
    description: 'Water ripple effect from center outward',
    defaultConfig: {count: 6, maxRadius: 200, interval: 12, color: 'primary'},
    intensity: 'low',
    tags: ['ripple', 'organic', 'center'],
  },
  {
    id: 'morph_playful',
    type: 'geometric_morph',
    label: 'Playful Morph',
    description: 'Bouncy shape morphing between circle/triangle/square',
    defaultConfig: {size: 120, speed: 1, shapes: ['circle', 'triangle', 'square'], color: 'accent'},
    intensity: 'medium',
    tags: ['playful', 'dynamic', 'brand'],
  },
  {
    id: 'morph_hypnotic',
    type: 'geometric_morph',
    label: 'Hypnotic Morph',
    description: 'Slow mesmerizing shape transitions',
    defaultConfig: {size: 160, speed: 0.4, shapes: ['circle', 'star', 'hexagon'], color: 'primary'},
    intensity: 'low',
    tags: ['hypnotic', 'mesmerizing', 'loop'],
  },
  {
    id: 'data_stream',
    type: 'data_flow',
    label: 'Data Stream',
    description: 'Flowing lines suggesting data/stats/numbers',
    defaultConfig: {lines: 12, speed: 1, direction: 'right', color: 'accent'},
    intensity: 'medium',
    tags: ['data', 'stats', 'tech', 'analytics'],
  },
  {
    id: 'data_cascade',
    type: 'data_flow',
    label: 'Data Cascade',
    description: 'Vertical cascading data lines for stat reveals',
    defaultConfig: {lines: 8, speed: 0.8, direction: 'down', color: 'primary'},
    intensity: 'medium',
    tags: ['data', 'cascade', 'vertical', 'stat'],
  },
  {
    id: 'burst_impact',
    type: 'energy_burst',
    label: 'Impact Burst',
    description: 'Radial energy burst from center for emphasis',
    defaultConfig: {lines: 20, maxLength: 250, color: 'accent'},
    intensity: 'high',
    tags: ['impact', 'burst', 'emphasis'],
  },
  {
    id: 'burst_subtle',
    type: 'energy_burst',
    label: 'Subtle Burst',
    description: 'Gentle radial pulse for soft emphasis',
    defaultConfig: {lines: 12, maxLength: 150, color: 'primary'},
    intensity: 'low',
    tags: ['subtle', 'pulse', 'emphasis'],
  },
  {
    id: 'orbital_rings',
    type: 'orbital',
    label: 'Orbital Rings',
    description: 'Concentric orbiting dots like atomic model',
    defaultConfig: {rings: 3, dots: 6, radius: 120, color: 'accent'},
    intensity: 'medium',
    tags: ['tech', 'orbital', 'science', 'precision'],
  },
  {
    id: 'orbital_dense',
    type: 'orbital',
    label: 'Dense Orbit',
    description: 'Many orbiting elements for complex tech feel',
    defaultConfig: {rings: 4, dots: 8, radius: 140, color: 'primary'},
    intensity: 'high',
    tags: ['complex', 'tech', 'dense'],
  },
  {
    id: 'text_explode',
    type: 'text_shatter',
    label: 'Text Explode',
    description: 'Characters shatter apart on entry for dramatic reveals',
    defaultConfig: {shatterDistance: 80, shatterAngle: 45, color: 'accent'},
    intensity: 'high',
    tags: ['dramatic', 'entry', 'text', 'reveal'],
  },
  {
    id: 'grid_scan',
    type: 'grid_pulse',
    label: 'Grid Scan',
    description: 'Pulsing grid lines like sci-fi interface',
    defaultConfig: {cells: 4, cellSize: 60, pulseSpeed: 1, color: 'primary'},
    intensity: 'medium',
    tags: ['grid', 'tech', 'scifi', 'interface'],
  },
  {
    id: 'text_shatter',
    type: 'text_shatter',
    label: 'Text Shatter',
    description: 'Characters explode outward then snap back into place for dramatic title reveals',
    defaultConfig: {count: 30, spread: 150, color: 'accent'},
    intensity: 'high',
    tags: ['text', 'shatter', 'dramatic', 'reveal'],
  },
  {
    id: 'glow_trail',
    type: 'glow_trail',
    label: 'Glow Trail',
    description: 'Particles that follow a curved path leaving luminous afterglow trails',
    defaultConfig: {count: 20, trail: 8, speed: 0.6, pathRadius: 120, color: 'accent'},
    intensity: 'medium',
    tags: ['glow', 'trail', 'particle', 'luminous'],
  },
  {
    id: 'kinetic_type_zoom',
    type: 'kinetic_type_zoom',
    label: 'Kinetic Type Zoom',
    description: 'Headline-scale emphasis pulse — rapid scale oscillation with motion blur feel',
    defaultConfig: {scale: 1.3, frequency: 2, rings: 3, color: 'primary'},
    intensity: 'high',
    tags: ['kinetic', 'type', 'zoom', 'headline', 'emphasis'],
  },
  {
    id: 'grid_pulse_fast',
    type: 'grid_pulse',
    label: 'Fast Grid Pulse',
    description: 'Rapid grid pulse for tech-heavy energy moments',
    defaultConfig: {cells: 6, cellSize: 50, pulseSpeed: 2.5, color: 'accent'},
    intensity: 'high',
    tags: ['fast', 'grid', 'tech', 'energy'],
  },
];

export function findMotionGraphic(id: string): MotionGraphicTemplate | undefined {
  return MOTION_GRAPHIC_CATALOG.find((t) => t.id === id);
}

export function findMotionGraphicsByTag(tag: string): MotionGraphicTemplate[] {
  return MOTION_GRAPHIC_CATALOG.filter((t) => t.tags.includes(tag));
}
