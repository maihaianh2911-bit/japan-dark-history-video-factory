import React, {useMemo} from 'react';
import {
	AbsoluteFill,
	interpolate,
	random,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {C, FONT, FONT_JP} from './theme';

/* ------------------------------------------------------------------ */
/* Hiệu ứng                                                             */
/* ------------------------------------------------------------------ */

/** Giá trị 0→1 kiểu "bật" (spring), bắt đầu từ khung `delay`. */
export const usePop = (delay = 0, stiff = 170) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (frame < delay) return 0;
	return spring({
		frame: frame - delay,
		fps,
		config: {damping: 13, stiffness: stiff, mass: 0.6},
	});
};

/** Nội suy có kẹp hai đầu. */
export const lerp = (f: number, a: number, b: number, from: number, to: number) =>
	interpolate(f, [a, b], [from, to], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

/** Đặt phần tử tại tâm (x, y), có hiệu ứng bật lên. */
export const Place: React.FC<{
	x: number;
	y: number;
	delay?: number;
	scale?: number;
	rotate?: number;
	children: React.ReactNode;
}> = ({x, y, delay = 0, scale = 1, rotate = 0, children}) => {
	const p = usePop(delay);
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				whiteSpace: 'nowrap',
				opacity: Math.min(1, p * 1.4),
				transform: `translate(-50%, -50%) scale(${scale * (0.6 + 0.4 * p)}) rotate(${rotate}deg)`,
			}}
		>
			{children}
		</div>
	);
};

/* ------------------------------------------------------------------ */
/* Nền & khung                                                           */
/* ------------------------------------------------------------------ */

export const StarBackground: React.FC = () => {
	const frame = useCurrentFrame();
	const {width, height} = useVideoConfig();
	const stars = useMemo(
		() =>
			new Array(150).fill(0).map((_, i) => ({
				x: random(`x${i}`) * width,
				y: random(`y${i}`) * height,
				r: 1 + random(`r${i}`) * 2.4,
				phase: random(`p${i}`) * Math.PI * 2,
				speed: 0.03 + random(`s${i}`) * 0.06,
				drift: 0.1 + random(`d${i}`) * 0.35,
			})),
		[width, height],
	);
	return (
		<AbsoluteFill
			style={{
				background:
					'radial-gradient(ellipse at 50% 38%, #1B2130 0%, #0D1017 55%, #06070A 100%)',
			}}
		>
			<svg width={width} height={height}>
				{stars.map((s, i) => (
					<circle
						key={i}
						cx={s.x}
						cy={(s.y - frame * s.drift + height) % height}
						r={s.r}
						fill="#fff"
						opacity={0.25 + 0.5 * (0.5 + 0.5 * Math.sin(frame * s.speed + s.phase))}
					/>
				))}
			</svg>
		</AbsoluteFill>
	);
};

export const ProgressBar: React.FC<{total: number}> = ({total}) => {
	const frame = useCurrentFrame();
	const {width} = useVideoConfig();
	return (
		<div
			style={{
				position: 'absolute',
				top: 0,
				left: 0,
				height: 10,
				width: (frame / total) * width,
				background: C.yellow,
				boxShadow: `0 0 18px ${C.yellow}`,
			}}
		/>
	);
};

export const Header: React.FC<{text: string}> = ({text}) => (
	<div
		style={{
			position: 'absolute',
			top: 110,
			width: '100%',
			display: 'flex',
			justifyContent: 'center',
		}}
	>
		<div
			style={{
				fontFamily: FONT,
				fontWeight: 800,
				fontSize: 30,
				letterSpacing: 4,
				color: C.muted,
				border: `2px solid #2A3142`,
				borderRadius: 999,
				padding: '10px 28px',
				background: 'rgba(12,15,21,0.6)',
			}}
		>
			{text}
		</div>
	</div>
);

/* ------------------------------------------------------------------ */
/* Phụ đề: *chữ* = tô vàng                                              */
/* ------------------------------------------------------------------ */

export type Sub = {from: number; to: number; text: string};

export const Subtitles: React.FC<{subs: Sub[]; top?: number}> = ({subs, top = 1300}) => {
	const frame = useCurrentFrame();
	const cur = subs.find((s) => frame >= s.from && frame < s.to);
	const p = usePop(cur ? cur.from : 0, 260);
	if (!cur) return null;
	const parts = cur.text.split(/(\*[^*]+\*)/).filter(Boolean);
	return (
		<div
			style={{
				position: 'absolute',
				top,
				width: '100%',
				padding: '0 80px',
				textAlign: 'center',
				fontFamily: FONT,
				fontWeight: 900,
				fontSize: 62,
				lineHeight: 1.25,
				color: C.white,
				textShadow: '0 4px 24px rgba(0,0,0,0.7)',
				opacity: Math.min(1, p * 1.5),
				transform: `translateY(${(1 - p) * 24}px)`,
			}}
		>
			{parts.map((t, i) =>
				t.startsWith('*') ? (
					<span key={i} style={{color: C.yellow}}>
						{t.slice(1, -1)}
					</span>
				) : (
					<span key={i}>{t}</span>
				),
			)}
		</div>
	);
};

/* ------------------------------------------------------------------ */
/* Ô đội bóng (chữ, không dùng logo thật)                               */
/* ------------------------------------------------------------------ */

export type Team = {label: string; bg: string; fg: string; sub?: string; jp?: boolean};

export const Tile: React.FC<{team: Team; size?: number}> = ({team, size = 180}) => (
	<div
		style={{
			width: size,
			height: size,
			borderRadius: size * 0.2,
			background: team.bg,
			boxShadow: '0 12px 36px rgba(0,0,0,0.45)',
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			gap: size * 0.02,
		}}
	>
		<div
			style={{
				fontFamily: team.jp ? FONT_JP : FONT,
				fontWeight: 900,
				fontSize: size * (team.label.length > 3 ? 0.26 : 0.32),
				color: team.fg,
				lineHeight: 1,
			}}
		>
			{team.label}
		</div>
		{team.sub ? (
			<div
				style={{
					fontFamily: FONT,
					fontWeight: 800,
					fontSize: size * 0.11,
					color: team.fg,
					opacity: 0.7,
				}}
			>
				{team.sub}
			</div>
		) : null}
	</div>
);

/* ------------------------------------------------------------------ */
/* Thẻ cầu thủ (ảnh giả: bóng người — thay bằng ảnh thật khi dựng)      */
/* ------------------------------------------------------------------ */

export type Player = {name: string; jp: string; color: string; team: Team; photo?: string};

export const PlayerCard: React.FC<{player: Player; w?: number}> = ({player, w = 360}) => {
	const h = w * 1.28;
	const gid = `g-${player.name.replace(/\W/g, '')}`;
	return (
		<div style={{position: 'relative', width: w, height: h}}>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					borderRadius: w * 0.07,
					border: `${w * 0.018}px solid ${player.color}`,
					overflow: 'hidden',
					boxShadow: `0 16px 50px rgba(0,0,0,0.55), 0 0 40px ${player.color}55`,
					background: '#151A24',
				}}
			>
				{player.photo ? (
					<img src={player.photo} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
				) : (
					<svg viewBox="0 0 100 128" style={{width: '100%', height: '100%'}}>
						<defs>
							<linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
								<stop offset="0" stopColor={player.color} stopOpacity="0.55" />
								<stop offset="1" stopColor="#10141C" stopOpacity="1" />
							</linearGradient>
						</defs>
						<rect width="100" height="128" fill={`url(#${gid})`} />
						<circle cx="50" cy="50" r="19" fill="rgba(255,255,255,0.22)" />
						<path d="M10 128 C12 92 30 78 50 78 C70 78 88 92 90 128 Z" fill="rgba(255,255,255,0.22)" />
					</svg>
				)}
				<div
					style={{
						position: 'absolute',
						left: 0,
						right: 0,
						bottom: 0,
						height: '42%',
						background: 'linear-gradient(transparent, rgba(0,0,0,0.88))',
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						justifyContent: 'flex-end',
						paddingBottom: w * 0.05,
					}}
				>
					<div style={{fontFamily: FONT_JP, fontWeight: 900, fontSize: w * 0.075, color: '#fff', opacity: 0.85}}>
						{player.jp}
					</div>
					<div
						style={{
							fontFamily: FONT,
							fontWeight: 900,
							fontSize: w * 0.12,
							color: '#fff',
							letterSpacing: 1,
							lineHeight: 1.05,
						}}
					>
						{player.name.toUpperCase()}
					</div>
				</div>
			</div>
			<div style={{position: 'absolute', top: -w * 0.09, right: -w * 0.09}}>
				<Tile team={player.team} size={w * 0.3} />
			</div>
		</div>
	);
};

/* ------------------------------------------------------------------ */
/* Nhãn, ngày, con dấu, bong bóng hỏi                                   */
/* ------------------------------------------------------------------ */

export const Tag: React.FC<{text: string; bg: string; fg?: string; size?: number; outline?: boolean}> = ({
	text,
	bg,
	fg = '#fff',
	size = 34,
	outline,
}) => (
	<div
		style={{
			fontFamily: FONT,
			fontWeight: 900,
			fontSize: size,
			color: outline ? bg : fg,
			background: outline ? 'rgba(12,15,21,0.7)' : bg,
			border: outline ? `3px solid ${bg}` : 'none',
			borderRadius: 999,
			padding: `${size * 0.28}px ${size * 0.75}px`,
			whiteSpace: 'nowrap',
			letterSpacing: 1,
		}}
	>
		{text}
	</div>
);

export const DatePill: React.FC<{text: string; size?: number; color?: string}> = ({text, size = 44, color = '#fff'}) => (
	<div
		style={{
			fontFamily: FONT,
			fontWeight: 900,
			fontSize: size,
			color,
			border: `4px solid ${color}`,
			borderRadius: 999,
			padding: `${size * 0.18}px ${size * 0.6}px`,
			background: 'rgba(12,15,21,0.75)',
		}}
	>
		{text}
	</div>
);

export const Stamp: React.FC<{text: string; color?: string; size?: number}> = ({text, color = C.yellow, size = 92}) => (
	<div
		style={{
			fontFamily: FONT,
			fontWeight: 900,
			fontSize: size,
			color,
			border: `${size * 0.08}px solid ${color}`,
			borderRadius: size * 0.18,
			padding: `${size * 0.06}px ${size * 0.3}px`,
			whiteSpace: 'nowrap',
			textShadow: `0 0 30px ${color}88`,
			boxShadow: `0 0 40px ${color}44`,
			background: 'rgba(12,15,21,0.55)',
		}}
	>
		{text}
	</div>
);

export const Bubble: React.FC<{text: string}> = ({text}) => (
	<div style={{position: 'relative'}}>
		<div
			style={{
				fontFamily: FONT,
				fontWeight: 900,
				fontSize: 56,
				color: C.ink,
				background: '#fff',
				borderRadius: 40,
				padding: '26px 48px',
				whiteSpace: 'nowrap',
				boxShadow: '0 16px 40px rgba(0,0,0,0.45)',
			}}
		>
			{text}
		</div>
		<div
			style={{
				position: 'absolute',
				left: 70,
				bottom: -34,
				width: 0,
				height: 0,
				borderLeft: '22px solid transparent',
				borderRight: '22px solid transparent',
				borderTop: '40px solid #fff',
			}}
		/>
	</div>
);
