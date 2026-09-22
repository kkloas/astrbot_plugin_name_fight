export function drawWeapon(ctx, weapon, ink, time) {
    ctx.save();
    ctx.strokeStyle = ink;
    ctx.fillStyle = '#e5e6db';
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    const line = (x1, y1, x2, y2, width, color = ink) => {
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    };
    if (weapon === 'unarmed') {
        line(0, -4, 3, 4, 4);
    }
    else if (weapon === 'spear') {
        line(-94, 0, 112, 0, 4, '#5c5747');
        ctx.beginPath();
        ctx.moveTo(103, -6);
        ctx.lineTo(140, 0);
        ctx.lineTo(103, 6);
        ctx.closePath();
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.stroke();
        const flutter = Math.sin(time / 110) * 6;
        line(100, 0, 75, 12 + flutter, 2.5, '#8d463a');
        line(100, 0, 77, 6 + flutter, 2, '#8d463a');
    }
    else if (weapon === 'brush') {
        line(-12, 0, 27, 0, 5);
        line(0, 0, 22, 0, 2, '#999783');
        ctx.fillStyle = '#dbdacd';
        ctx.beginPath();
        ctx.moveTo(26, -5);
        ctx.lineTo(45, 0);
        ctx.lineTo(26, 5);
        ctx.closePath();
        ctx.fill();
        line(40, 0, 45, 0, 2, '#883e31');
    }
    else if (weapon === 'needles') {
        line(-5, -5, 16, -5, 3);
        line(6, -3, 25, -7, 1.5);
        line(7, 1, 28, 0, 1.5);
    }
    else if (weapon === 'zither') {
        ctx.fillStyle = '#41483c';
        ctx.beginPath();
        ctx.roundRect(-60, -9, 125, 22, 6);
        ctx.fill();
        for (let i = 0; i < 6; i++)
            line(-52, -5 + i * 2.5, 55, -5 + i * 2.5, .65, '#c6c4ab');
        line(48, -10, 48, 12, 2, '#9f9b84');
    }
    else {
        line(-17, 0, 3, 0, weapon === 'katana' ? 6 : 5);
        line(2, -8, 2, 8, 3);
        ctx.beginPath();
        ctx.moveTo(5, -2.5);
        if (weapon === 'blade') {
            ctx.quadraticCurveTo(56, -6, 104, -23);
            ctx.quadraticCurveTo(92, 0, 76, 9);
            ctx.lineTo(5, 5);
        }
        else if (weapon === 'katana') {
            ctx.quadraticCurveTo(62, -1, 111, -14);
            ctx.lineTo(108, -8);
            ctx.quadraticCurveTo(56, 6, 5, 3);
        }
        else {
            ctx.lineTo(85, -1.5);
            ctx.lineTo(99, 0);
            ctx.lineTo(85, 2);
            ctx.lineTo(5, 2.5);
        }
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.2;
        ctx.stroke();
    }
    ctx.restore();
}
