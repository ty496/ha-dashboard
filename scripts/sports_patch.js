// Shared transform: adds the Sports subview, live-game conditionals on Home, and a Scores tile.
module.exports = function patch(cfg) {
  const teams = ['broncos','bears','avalanche','fsu','iowa','rockies'];
  const card = (t) => ({ type: 'custom:teamtracker-card', entity: 'sensor.' + t, grid_options: { columns: 'full' } });
  // 1. Sports subview
  cfg.views = cfg.views.filter(v => v.path !== 'sports');
  cfg.views.push({ title: 'Scores', path: 'sports', subview: true, icon: 'mdi:scoreboard', type: 'sections', max_columns: 3, dense_section_placement: true,
    sections: [
      { type: 'grid', cards: [ { type: 'heading', heading: 'Football', icon: 'mdi:football' }, card('broncos'), card('bears') ] },
      { type: 'grid', cards: [ { type: 'heading', heading: 'College', icon: 'mdi:school' }, card('fsu'), card('iowa') ] },
      { type: 'grid', cards: [ { type: 'heading', heading: 'Hockey and baseball', icon: 'mdi:hockey-puck' }, card('avalanche'), card('rockies') ] },
    ] });
  // 2. Home view
  const home = cfg.views.find(v => v.path === 'home') || cfg.views[0];
  const secs = home.sections;
  const col1 = secs[0], calSec = secs.find(s => (s.cards||[]).some(c => c.type === 'custom:atomic-calendar-revive')), roomSec = secs.find(s => (s.cards||[]).some(c => c.type === 'area'));
  // Scores tile in column 1 (navigates to the subview)
  col1.cards = col1.cards.filter(c => !(c.type === 'button' && c.name === 'Scores'));
  col1.cards.push({ type: 'button', name: 'Scores', icon: 'mdi:scoreboard-outline', show_state: false, tap_action: { action: 'navigate', navigation_path: '/dashboard-show/sports' }, grid_options: { columns: 'full', rows: 1 } });
  // Broncos stays under the calendar; the other five appear under the rooms only while a game is live
  roomSec.cards = roomSec.cards.filter(c => !(c.type === 'conditional' && c.card?.type === 'custom:teamtracker-card'));
  for (const t of teams.filter(t => t !== 'broncos')) roomSec.cards.push({ type: 'conditional', conditions: [ { condition: 'state', entity: 'sensor.' + t, state: 'IN' } ], card: card(t) });
  return cfg;
};
