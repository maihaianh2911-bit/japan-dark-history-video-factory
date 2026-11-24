import '@fontsource/be-vietnam-pro/800.css';
import '@fontsource/be-vietnam-pro/900.css';
import '@fontsource/noto-sans-jp/900.css';
import {continueRender, delayRender} from 'remotion';

export const FONT = '"Be Vietnam Pro", "Noto Sans JP", sans-serif';
export const FONT_JP = '"Noto Sans JP", "Be Vietnam Pro", sans-serif';

export const C = {
	yellow: '#FFC83D',
	red: '#FF4D4F',
	green: '#2BD9A0',
	white: '#FFFFFF',
	ink: '#0C0F15',
	muted: '#8A93A6',
};

// Chờ font tải xong rồi mới render, tránh khung đầu bị font mặc định
const fontHandle = delayRender('Tải font');
Promise.all([
	document.fonts.load(`900 64px "Be Vietnam Pro"`, 'Aạờểỷ Đđ 0123'),
	document.fonts.load(`800 64px "Be Vietnam Pro"`, 'Aạờểỷ Đđ 0123'),
	document.fonts.load(`900 64px "Noto Sans JP"`, '佐藤輝明平良海馬阪神西武日本'),
])
	.then(() => continueRender(fontHandle))
	.catch(() => continueRender(fontHandle));
