# Material assets

Source: `web/frontend/Material.png`

This pass removes section titles, number labels, and nearby explanatory text from the sliced assets. The remaining files are reusable visual pieces for the web UI.

## Direct-use groups

- `01_paper_texture/paper_texture.png`: paper texture for panels and cards.
- `03_ink_backgrounds/*.png`: ink landscape strips for battle stage, side panels, and empty states.
- `04_title_marks/black_vertical_brush.png`: vertical ink brush plate for battle-side name plates.
- `04_title_marks/gray_vertical_plate.png`: vertical gray plate for muted tags.
- `10_dividers/*.png`: separator lines for battle log and detail sections.
- `11_buttons/*.png`: blank button decoration backgrounds.

## Fine UI groups

- `06_stat_icons/*_light.png`: stat icons for light paper panels.
- `06_stat_icons/*_dark.png`: stat icons for dark side panels.
- `07_stat_bars/*.png`: pre-rendered ink stat bars by quality and stat row.
- `08_stamps/*.png`: stamp marks and ink dots for quality, selected state, or result marks.
- `09_ornaments/*.png`: bamboo, pine, birds, and leaves for restrained decoration.
- `05_weapon_silhouettes/*.png`: weapon silhouettes for martial-art cards or battle move cues.

## Notes

- The hanging tag with built-in Chinese text was intentionally not sliced. Text should be rendered by the browser.
- Section headings and label text from the source sheet were intentionally excluded.
- Most files still keep the original white background. Use CSS blend modes first; do transparent cutouts only for assets that need to float over dark panels.
