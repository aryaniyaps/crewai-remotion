import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {createTikTokStyleCaptions} from '@remotion/captions';
import type {Caption, TikTokToken} from '@remotion/captions';
import type {ThemeTokens} from '../design/tokens';

type CaptionWord = {text: string; start_ms: number; end_ms: number};

const MIN_VISIBLE_TOKENS = 3;
const TARGET_VISIBLE_TOKENS = 5;
const MAX_VISIBLE_TOKENS = 7;

type CaptionToken = Pick<TikTokToken, 'text' | 'fromMs' | 'toMs'>;

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

const findActiveTokenIndex = (tokens: CaptionToken[], frameMs: number) => {
  const currentIndex = tokens.findIndex(
    (token) => frameMs >= token.fromMs && frameMs < token.toMs,
  );
  if (currentIndex >= 0) return currentIndex;

  let nearestIndex = 0;
  let nearestDistance = Number.POSITIVE_INFINITY;
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    const distance =
      frameMs < token.fromMs ? token.fromMs - frameMs : frameMs - token.toMs;
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = i;
    }
  }

  return nearestIndex;
};

const createActiveTokenWindow = (tokens: CaptionToken[], activeIndex: number) => {
  const visibleCount = Math.min(
    tokens.length,
    clamp(TARGET_VISIBLE_TOKENS, MIN_VISIBLE_TOKENS, MAX_VISIBLE_TOKENS),
  );
  const start = clamp(
    activeIndex - Math.floor(visibleCount / 2),
    0,
    Math.max(tokens.length - visibleCount, 0),
  );

  return {start, tokens: tokens.slice(start, start + visibleCount)};
};

/**
 * CaptionLayer — mobile karaoke captions.
 *
 * Uses @remotion/captions for timing pages, then renders only a compact active
 * word window so long transcripts never become multi-line blocks.
 */
export const CaptionLayer: React.FC<{
  theme: ThemeTokens;
  words: CaptionWord[];
}> = ({theme, words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const frameMs = (frame / fps) * 1000;

  // Map to full Caption type expected by @remotion/captions
  const captions: Caption[] = useMemo(
    () =>
      words.map((w) => ({
        text: w.text,
        startMs: w.start_ms,
        endMs: w.end_ms,
        timestampMs: null,
        confidence: null,
      })),
    [words],
  );

  // Group words using TikTok-style caption grouper
  const result = useMemo(() => {
    if (captions.length === 0) return {pages: []};
    return createTikTokStyleCaptions({
      captions,
      combineTokensWithinMilliseconds: 800,
    });
  }, [captions]);

  // Find active page
  const activePage = result.pages.find(
    (p) => frameMs >= p.startMs && frameMs < p.startMs + p.durationMs,
  );
  if (!activePage || !activePage.tokens || activePage.tokens.length === 0) {
    return null;
  }

  const pageTokens = activePage.tokens;
  const activeTokenIndex = findActiveTokenIndex(pageTokens, frameMs);
  const visibleWindow = createActiveTokenWindow(pageTokens, activeTokenIndex);
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 220,
        paddingLeft: 60,
        paddingRight: 60,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '6px 14px',
          width: 'fit-content',
          maxWidth: 900,
          maxHeight: 118,
          overflow: 'hidden',
          padding: '18px 28px 20px',
          borderRadius: 30,
          background: 'rgba(6, 10, 24, 0.66)',
          boxShadow: '0 18px 44px rgba(0, 0, 0, 0.32)',
        }}
      >
        {visibleWindow.tokens.map((token, i) => {
          const tokenIndex = visibleWindow.start + i;
          const isCurrent = tokenIndex === activeTokenIndex;
          const isPast = tokenIndex < activeTokenIndex;
          return (
            <span
              key={`${token.fromMs}-${tokenIndex}`}
              style={{
                flex: '0 1 auto',
                fontSize: 44,
                fontWeight: 800,
                fontFamily: theme.font_body,
                color: isCurrent
                  ? theme.caption_highlight
                  : isPast
                    ? '#ffffff'
                    : 'rgba(255, 255, 255, 0.58)',
                textShadow: '0 3px 12px rgba(0,0,0,0.72)',
                lineHeight: 1.05,
                letterSpacing: '-0.02em',
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
