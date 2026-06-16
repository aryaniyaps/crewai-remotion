import React from 'react';
import {useCurrentFrame} from 'remotion';
import {parallaxOffset} from '../design/motion';

/**
 * ParallaxLayer — creates depth through multi-plane parallax motion.
 *
 * Wraps children with three depth planes that move at different rates,
 * simulating a subtle 3D parallax effect. Works as a composition wrapper.
 *
 * Back plane: slow drift (0.3x)
 * Mid plane: medium drift (0.6x)
 * Front plane: faster drift (1.2x)
 */
export const ParallaxLayer: React.FC<{
  speed?: number;
  children: React.ReactNode;
}> = ({speed = 1, children}) => {
  const frame = useCurrentFrame();

  const back = parallaxOffset(frame, 'back', speed);
  const mid = parallaxOffset(frame, 'mid', speed);
  const front = parallaxOffset(frame, 'front', speed);

  // We wrap in a single transform that applies a subtle shift.
  // The caller places content in different layers via stacking.
  // Here we provide the offset via CSS custom properties so children can
  // use them without prop drilling.
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        '--parallax-back-x': `${back.x}px`,
        '--parallax-back-y': `${back.y}px`,
        '--parallax-mid-x': `${mid.x}px`,
        '--parallax-mid-y': `${mid.y}px`,
        '--parallax-front-x': `${front.x}px`,
        '--parallax-front-y': `${front.y}px`,
        translate: `${mid.x}px ${mid.y}px`,
      } as React.CSSProperties}
    >
      {children}
    </div>
  );
};
