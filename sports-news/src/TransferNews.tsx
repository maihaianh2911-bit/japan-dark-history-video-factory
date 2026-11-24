import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import {
	Bubble,
	DatePill,
	Header,
	lerp,
	Place,
	Player,
	PlayerCard,
	ProgressBar,
	Stamp,
	StarBackground,
	Sub,
	Subtitles,
	Tag,
	Team,
	Tile,
	usePop,
} from './components';
import {C, FONT} from './theme';

/*
 * BẢN DEMO — tin NPB → MLB mùa đông 2026 (dữ liệu theo báo Nhật đến 21/11/2026).
 * 30 khung hình = 1 giây. Mỗi cảnh dài 4 giây (120 khung), cảnh mở đầu 3 giây.
 */

const NPB: Team = {label: 'NPB', sub: 'NHẬT BẢN', bg: '#fff', fg: '#111'};
const MLB: Team = {label: 'MLB', sub: 'MỸ', bg: '#fff', fg: '#0B3D91'};
const HANSHIN: Team = {label: '阪神', bg: '#FFD100', fg: '#111', jp: true};
const SEIBU: Team = {label: '西武', bg: '#0B3B8C', fg: '#fff', jp: true};
const PHI: Team = {label: 'PHI', bg: '#fff', fg: '#E81828'};
const NYM: Team = {label: 'NYM', bg: '#002D72', fg: '#FF5910'};
const NYY: Team = {label: 'NYY', bg: '#0C2340', fg: '#fff'};

const SATO: Player = {name: 'Sato', jp: '佐藤輝明', color: '#FFD100', team: HANSHIN};
const TAIRA: Player = {name: 'Taira', jp: '平良海馬', color: '#3B82F6', team: SEIBU};

const SCENES = [
	{id: 'hook', len: 90},
	{id: 'bridge', len: 120},
	{id: 'sato', len: 120},
	{id: 'taira', len: 120},
	{id: 'interest', len: 120},
	{id: 'deadline', len: 120},
	{id: 'end', len: 120},
];
export const TOTAL_FRAMES = SCENES.reduce((a, s) => a + s.len, 0);
const START: Record<string, number> = {};
SCENES.reduce((acc, s) => ((START[s.id] = acc), acc + s.len), 0);

const SUBS: Sub[] = [
	{from: 0, to: 45, text: 'Ngày *1/12*,'},
	{from: 45, to: 90, text: 'MLB có thể *khóa cửa*.'},
	{from: 90, to: 150, text: 'Và hai ngôi sao *Nhật Bản*'},
	{from: 150, to: 210, text: 'đang chạy đua với thời gian.'},
	{from: 210, to: 270, text: 'Hanshin chính thức để *Sato Teruaki*'},
	{from: 270, to: 330, text: 'sang Mỹ theo diện *posting*.'},
	{from: 330, to: 390, text: '11 ngày sau, *Seibu* gật đầu'},
	{from: 390, to: 450, text: 'với *Taira Kaima*, ERA chỉ *1.36*.'},
	{from: 450, to: 510, text: '*Phillies*, *Mets*, *Yankees*'},
	{from: 510, to: 570, text: 'đều được cho là muốn có Sato.'},
	{from: 570, to: 630, text: 'Thời hạn thường là *45 ngày*,'},
	{from: 630, to: 690, text: 'nhưng lockout có thể cắt còn *1/12*.'},
	{from: 690, to: 750, text: 'Theo bạn, ai ký hợp đồng trước:'},
	{from: 750, to: 810, text: '*Sato* hay *Taira*?'},
];

/* ------------------------------------------------------------------ */

const FadeIn: React.FC<{children: React.ReactNode}> = ({children}) => {
	const f = useCurrentFrame();
	return <AbsoluteFill style={{opacity: lerp(f, 0, 6, 0, 1)}}>{children}</AbsoluteFill>;
};

const Padlock: React.FC<{closeAt: number}> = ({closeAt}) => {
	const f = useCurrentFrame();
	const shackle = lerp(f, closeAt, closeAt + 8, -42, 0);
	return (
		<svg width={240} height={290} viewBox="0 0 240 290">
			<path
				d="M62 130 V88 a58 58 0 0 1 116 0 V130"
				fill="none"
				stroke={C.yellow}
				strokeWidth={24}
				strokeLinecap="round"
				transform={`translate(0 ${shackle})`}
			/>
			<rect x={28} y={124} width={184} height={150} rx={30} fill={C.yellow} />
			<circle cx={120} cy={188} r={18} fill={C.ink} />
			<rect x={112} y={192} width={16} height={44} rx={7} fill={C.ink} />
		</svg>
	);
};

const HookScene: React.FC = () => (
	<FadeIn>
		<Place x={540} y={460} delay={0}>
			<Padlock closeAt={48} />
		</Place>
		<Place x={540} y={760} delay={6}>
			<DatePill text="01/12" size={70} />
		</Place>
		<Place x={540} y={960} delay={50} rotate={-5}>
			<Stamp text="MLB KHÓA CỬA?" color={C.red} />
		</Place>
	</FadeIn>
);

const BridgeScene: React.FC = () => {
	const f = useCurrentFrame();
	const P0 = {x: 250, y: 720};
	const P1 = {x: 540, y: 330};
	const P2 = {x: 830, y: 720};
	const dot = (t: number) => ({
		x: (1 - t) ** 2 * P0.x + 2 * (1 - t) * t * P1.x + t ** 2 * P2.x,
		y: (1 - t) ** 2 * P0.y + 2 * (1 - t) * t * P1.y + t ** 2 * P2.y,
	});
	const arcOpacity = lerp(f, 10, 25, 0, 1);
	const dots = [lerp(f, 20, 80, 0, 1), lerp(f, 40, 100, 0, 1)].map(dot);
	return (
		<FadeIn>
			<svg width={1080} height={1920} style={{position: 'absolute'}}>
				<path
					d={`M${P0.x} ${P0.y} Q${P1.x} ${P1.y} ${P2.x} ${P2.y}`}
					fill="none"
					stroke={C.yellow}
					strokeWidth={8}
					strokeDasharray="4 22"
					strokeLinecap="round"
					opacity={arcOpacity}
				/>
				{dots.map((d, i) => (
					<circle key={i} cx={d.x} cy={d.y} r={16} fill={C.yellow} opacity={arcOpacity} style={{filter: `drop-shadow(0 0 14px ${C.yellow})`}} />
				))}
			</svg>
			<Place x={P0.x} y={P0.y + 40} delay={0}>
				<Tile team={NPB} size={220} />
			</Place>
			<Place x={P2.x} y={P2.y + 40} delay={8}>
				<Tile team={MLB} size={220} />
			</Place>
			<Place x={540} y={1000} delay={30}>
				<Tag text="2 NGÔI SAO · 1 MÙA ĐÔNG" bg={C.yellow} outline size={38} />
			</Place>
		</FadeIn>
	);
};

const SatoScene: React.FC = () => (
	<FadeIn>
		<Place x={540} y={330} delay={0}>
			<DatePill text="19/10" />
		</Place>
		<Place x={540} y={680} delay={6}>
			<PlayerCard player={SATO} w={380} />
		</Place>
		<Place x={540} y={1010} delay={24}>
			<Tag text="CHÍNH THỨC" bg={C.green} fg={C.ink} />
		</Place>
		<Place x={540} y={860} delay={62} rotate={-6}>
			<Stamp text="POSTING" />
		</Place>
	</FadeIn>
);

const TairaScene: React.FC = () => {
	const f = useCurrentFrame();
	const satoX = lerp(f, 0, 12, 540, 300);
	const satoScale = lerp(f, 0, 12, 1, 0.78);
	const arrow = usePop(18);
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', left: satoX, top: 680, transform: `translate(-50%, -50%) scale(${satoScale})`}}>
				<PlayerCard player={SATO} w={380} />
			</div>
			<Place x={300} y={385} delay={4}>
				<DatePill text="19/10" size={36} />
			</Place>
			<Place x={780} y={385} delay={14}>
				<DatePill text="30/10" size={36} />
			</Place>
			<Place x={780} y={680} delay={10} scale={0.78}>
				<PlayerCard player={TAIRA} w={380} />
			</Place>
			<div style={{position: 'absolute', left: 470, top: 640, width: 140, opacity: arrow}}>
				<div style={{fontFamily: FONT, fontWeight: 900, fontSize: 30, color: C.yellow, textAlign: 'center'}}>+11 ngày</div>
				<svg width={140} height={40}>
					<line x1={6} y1={20} x2={112 * arrow + 6} y2={20} stroke={C.yellow} strokeWidth={6} strokeLinecap="round" />
					<path d="M112 6 L134 20 L112 34 Z" fill={C.yellow} opacity={arrow > 0.9 ? 1 : 0} />
				</svg>
			</div>
			<Place x={780} y={1000} delay={66}>
				<Tag text="ERA 1.36" bg={C.yellow} fg={C.ink} />
			</Place>
			<Place x={300} y={1000} delay={6}>
				<Tag text="POSTING" bg={C.yellow} outline size={30} />
			</Place>
		</AbsoluteFill>
	);
};

const InterestScene: React.FC = () => {
	const f = useCurrentFrame();
	const center = {x: 540, y: 690};
	const tiles: {team: Team; x: number; y: number; delay: number}[] = [
		{team: PHI, x: 180, y: 520, delay: 2},
		{team: NYM, x: 900, y: 520, delay: 12},
		{team: NYY, x: 540, y: 300, delay: 22},
	];
	return (
		<FadeIn>
			<svg width={1080} height={1920} style={{position: 'absolute'}}>
				{tiles.map((t, i) => (
					<line
						key={i}
						x1={t.x}
						y1={t.y}
						x2={center.x}
						y2={center.y}
						stroke="#fff"
						strokeWidth={5}
						strokeDasharray="10 14"
						opacity={0.45 * lerp(f, t.delay + 4, t.delay + 14, 0, 1)}
					/>
				))}
			</svg>
			<Place x={center.x} y={center.y} delay={0} scale={0.85}>
				<PlayerCard player={SATO} w={380} />
			</Place>
			{tiles.map((t, i) => (
				<Place key={i} x={t.x} y={t.y} delay={t.delay}>
					<div style={{position: 'relative'}}>
						<Tile team={t.team} size={170} />
						<div
							style={{
								position: 'absolute',
								right: -18,
								top: -18,
								width: 56,
								height: 56,
								borderRadius: 999,
								background: C.yellow,
								color: C.ink,
								fontFamily: FONT,
								fontWeight: 900,
								fontSize: 40,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
							}}
						>
							?
						</div>
					</div>
				</Place>
			))}
			<Place x={540} y={1010} delay={62}>
				<Tag text="TIN ĐỒN · báo Nhật" bg={C.yellow} outline />
			</Place>
		</FadeIn>
	);
};

const DeadlineScene: React.FC = () => {
	const f = useCurrentFrame();
	const x0 = 120;
	const w = 840;
	const fill = lerp(f, 6, 50, 0, 1);
	const cut = 30 / 45; // 01/11 → 01/12 = 30 ngày trên tổng 45 ngày
	const cutP = usePop(64);
	return (
		<FadeIn>
			<Place x={540} y={420} delay={0}>
				<div style={{fontFamily: FONT, fontWeight: 800, fontSize: 36, letterSpacing: 4, color: C.muted}}>HẠN ĐÀM PHÁN POSTING</div>
			</Place>
			<Place x={540} y={540} delay={4}>
				<div style={{fontFamily: FONT, fontWeight: 900, fontSize: 110, color: C.yellow}}>45 NGÀY</div>
			</Place>
			<div style={{position: 'absolute', left: x0, top: 668, width: w, height: 28, borderRadius: 99, background: '#232A38'}} />
			<div
				style={{
					position: 'absolute',
					left: x0,
					top: 668,
					width: w * fill,
					height: 28,
					borderRadius: 99,
					background: C.yellow,
					boxShadow: `0 0 20px ${C.yellow}88`,
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: x0 + w * cut,
					top: 668,
					width: w * (1 - cut),
					height: 28,
					borderRadius: '0 99px 99px 0',
					background: `repeating-linear-gradient(135deg, ${C.red} 0 10px, #3a1418 10px 20px)`,
					opacity: cutP,
				}}
			/>
			<div style={{position: 'absolute', left: x0 + w * cut - 4, top: 630, width: 8, height: 104, borderRadius: 4, background: C.red, opacity: cutP}} />
			<Place x={x0} y={760} delay={6}>
				<div style={{fontFamily: FONT, fontWeight: 900, fontSize: 36, color: '#fff'}}>01/11</div>
			</Place>
			<Place x={x0 + w} y={760} delay={10}>
				<div style={{fontFamily: FONT, fontWeight: 900, fontSize: 36, color: '#fff'}}>16/12</div>
			</Place>
			<Place x={x0 + w * cut} y={810} delay={64}>
				<Tag text="01/12 · LOCKOUT?" bg={C.red} size={34} />
			</Place>
			<Place x={540} y={1010} delay={74} rotate={-4}>
				<Stamp text="CÓ THỂ RÚT NGẮN" color={C.red} size={74} />
			</Place>
		</FadeIn>
	);
};

const EndScene: React.FC = () => (
	<FadeIn>
		<Place x={300} y={600} delay={0} scale={0.78}>
			<PlayerCard player={SATO} w={380} />
		</Place>
		<Place x={780} y={600} delay={6} scale={0.78}>
			<PlayerCard player={TAIRA} w={380} />
		</Place>
		<Place x={540} y={600} delay={14}>
			<div
				style={{
					width: 110,
					height: 110,
					borderRadius: 999,
					background: C.yellow,
					color: C.ink,
					fontFamily: FONT,
					fontWeight: 900,
					fontSize: 46,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					boxShadow: `0 0 40px ${C.yellow}88`,
				}}
			>
				VS
			</div>
		</Place>
		<Place x={540} y={980} delay={22}>
			<Bubble text="Ai ký hợp đồng trước?" />
		</Place>
	</FadeIn>
);

const SCENE_COMPONENTS: Record<string, React.FC> = {
	hook: HookScene,
	bridge: BridgeScene,
	sato: SatoScene,
	taira: TairaScene,
	interest: InterestScene,
	deadline: DeadlineScene,
	end: EndScene,
};

export const TransferNews: React.FC = () => (
	<AbsoluteFill style={{backgroundColor: C.ink}}>
		<StarBackground />
		{SCENES.map((s) => {
			const Comp = SCENE_COMPONENTS[s.id];
			return (
				<Sequence key={s.id} from={START[s.id]} durationInFrames={s.len} layout="none">
					<AbsoluteFill>
						<Comp />
					</AbsoluteFill>
				</Sequence>
			);
		})}
		<Header text="BẢN TIN CHUYỂN NHƯỢNG · NPB → MLB" />
		<Subtitles subs={SUBS} />
		<ProgressBar total={TOTAL_FRAMES} />
	</AbsoluteFill>
);
