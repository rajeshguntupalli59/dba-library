// Renders Chapter 1 scenes into a container. `renderScenarioScene` and
// `renderQuizScene` are generic and reusable by any future chapter; the two
// animation scenes are custom per concept, dispatched by scene id.
//
// Motion helpers below are small and dependency-free (native Web Animations
// API + requestAnimationFrame), matching this repo's zero-build-step,
// zero-dependency posture. Every spatial animation checks
// prefers-reduced-motion and falls back to an instant, still-legible state
// change — color/opacity transitions are left in either way since they
// aren't spatial movement.

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function animateValue(node, from, to, { duration = 450, format = (v) => String(v) } = {}) {
  if (from === to || prefersReducedMotion()) {
    node.textContent = format(to);
    return;
  }
  const start = performance.now();
  let done = false;
  function finish() {
    if (done) return;
    done = true;
    node.textContent = format(to);
  }
  function tick(now) {
    if (done) return;
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out-cubic
    node.textContent = format(Math.round(from + (to - from) * eased));
    if (t < 1) requestAnimationFrame(tick);
    else finish();
  }
  requestAnimationFrame(tick);
  // Safety net: guarantee the exact final value lands even if
  // requestAnimationFrame is suspended (backgrounded tab, no compositing)
  // for the animation's duration.
  setTimeout(finish, duration + 100);
}

function fadeText(node, newText) {
  if (prefersReducedMotion()) {
    node.textContent = newText;
    return;
  }
  // The text swap is the correctness-critical part; it must happen even if
  // the animation itself is paused (backgrounded tab, no compositing), so
  // it's driven by a plain timer rather than the animation's finish event.
  node.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 120, easing: 'ease-out' });
  setTimeout(() => {
    node.textContent = newText;
    node.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 220, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' });
  }, 120);
}

function pulseElement(node) {
  if (prefersReducedMotion()) return;
  node.animate(
    [{ transform: 'scale(1)' }, { transform: 'scale(1.03)' }, { transform: 'scale(1)' }],
    { duration: 300, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }
  );
}

function shakeElement(node) {
  if (prefersReducedMotion()) return;
  node.animate(
    [
      { transform: 'translateX(0)' },
      { transform: 'translateX(-6px)' },
      { transform: 'translateX(6px)' },
      { transform: 'translateX(-4px)' },
      { transform: 'translateX(4px)' },
      { transform: 'translateX(0)' },
    ],
    { duration: 400, easing: 'ease-out' }
  );
}

function appendFeedbackIcon(btn, correct) {
  const icon = el('span', `mr-2 inline-block ${correct ? 'text-emerald-300' : 'text-red-300'}`, correct ? '✓' : '✗');
  btn.prepend(icon);
  if (!prefersReducedMotion()) {
    icon.animate(
      [{ opacity: 0, transform: 'scale(0.5)' }, { opacity: 1, transform: 'scale(1)' }],
      { duration: 250, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }
    );
  }
}

// Slides a small labeled token from `fromEl` to `toEl`, both measured
// relative to `wrapperEl` (which must be the shared positioned ancestor).
// Calls `onDone` when the motion (or its reduced-motion equivalent) settles.
function animateTokenTransfer(wrapperEl, fromEl, toEl, label, onDone) {
  if (prefersReducedMotion()) {
    onDone();
    return;
  }
  const wrapperRect = wrapperEl.getBoundingClientRect();
  const fromRect = fromEl.getBoundingClientRect();
  const toRect = toEl.getBoundingClientRect();
  const startX = fromRect.left + fromRect.width / 2 - wrapperRect.left;
  const startY = fromRect.top + fromRect.height / 2 - wrapperRect.top;
  const endX = toRect.left + toRect.width / 2 - wrapperRect.left;
  const endY = toRect.top + toRect.height / 2 - wrapperRect.top;
  const midX = (startX + endX) / 2;
  const midY = Math.min(startY, endY) - 28;

  const token = el(
    'div',
    'absolute px-2.5 py-1 rounded-full bg-emerald-500 text-gray-950 text-xs font-bold shadow-lg shadow-emerald-500/40 pointer-events-none whitespace-nowrap',
    label
  );
  token.style.left = '0px';
  token.style.top = '0px';
  wrapperEl.appendChild(token);

  const duration = 650;
  token.animate(
    [
      { transform: `translate(${startX}px, ${startY}px) translate(-50%, -50%) scale(1)`, opacity: 1 },
      { transform: `translate(${midX}px, ${midY}px) translate(-50%, -50%) scale(1.15)`, opacity: 1, offset: 0.5 },
      { transform: `translate(${endX}px, ${endY}px) translate(-50%, -50%) scale(1)`, opacity: 1 },
    ],
    { duration, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }
  );
  // The resulting balance update (via onDone) must happen even if this
  // animation is paused by the browser (backgrounded tab, no compositing),
  // so cleanup and onDone are driven by a plain timer, not animation.onfinish.
  setTimeout(() => {
    token.remove();
    onDone();
  }, duration);
}

function renderAcidTestScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.intro));
  if (scene.simulationNote) {
    container.appendChild(el('p', 'text-xs text-gray-500 italic mb-6', scene.simulationNote));
  }

  const badgeRow = el('div', 'flex gap-2 mb-6');
  const letters = ['A', 'C', 'I', 'D'];
  const badges = {};
  letters.forEach((letter) => {
    const badge = el('span', 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold transition-colors duration-300', letter);
    badges[letter] = badge;
    badgeRow.appendChild(badge);
  });
  container.appendChild(badgeRow);

  const balancesRow = el('div', 'relative flex gap-6 mb-6');
  const boxA = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center transition-colors duration-300');
  const boxB = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center transition-colors duration-300');
  boxA.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account A'));
  boxB.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account B'));
  const balA = el('div', 'text-2xl font-bold text-white');
  const balB = el('div', 'text-2xl font-bold text-white');
  boxA.appendChild(balA);
  boxB.appendChild(balB);
  balancesRow.appendChild(boxA);
  balancesRow.appendChild(boxB);
  container.appendChild(balancesRow);

  const narration = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[4.5rem]');
  container.appendChild(narration);

  const controls = el('div', 'flex items-center gap-3');
  const crashBtn = el('button', 'px-4 py-2 rounded-lg border border-red-800/60 text-red-300 hover:bg-red-900/30 transition text-sm', 'Simulate a crash here');
  const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Next');
  controls.appendChild(crashBtn);
  controls.appendChild(nextBtn);
  container.appendChild(controls);

  let stepIndex = 0;

  function paintBadges(activeLetter) {
    letters.forEach((letter) => {
      badges[letter].className = letter === activeLetter
        ? 'px-3 py-1 rounded-full border border-blue-500 bg-blue-600/20 text-blue-300 text-sm font-bold transition-colors duration-300'
        : 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold transition-colors duration-300';
    });
  }

  function paintStep(step, prevStep) {
    fadeText(narration, step.narration);
    paintBadges(step.acidLetter);
    crashBtn.disabled = stepIndex !== scene.crashStep;
    crashBtn.classList.toggle('opacity-30', crashBtn.disabled);
    crashBtn.classList.toggle('cursor-not-allowed', crashBtn.disabled);

    if (!prevStep) {
      balA.textContent = `$${step.balances.a}`;
      balB.textContent = `$${step.balances.b}`;
      return;
    }

    const deltaB = step.balances.b - prevStep.balances.b;
    if (deltaB > 0) {
      // Money is arriving at B this step — the token physically travels, then the number follows.
      animateValue(balA, prevStep.balances.a, step.balances.a, { duration: 300, format: (v) => `$${v}` });
      animateTokenTransfer(balancesRow, boxA, boxB, `$${deltaB}`, () => {
        animateValue(balB, prevStep.balances.b, step.balances.b, { duration: 350, format: (v) => `$${v}` });
      });
    } else {
      animateValue(balA, prevStep.balances.a, step.balances.a, { duration: 400, format: (v) => `$${v}` });
      animateValue(balB, prevStep.balances.b, step.balances.b, { duration: 400, format: (v) => `$${v}` });
    }
  }

  function finish() {
    controls.innerHTML = '';
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
    done.addEventListener('click', () => onComplete(scene.xp));
    controls.appendChild(done);
  }

  crashBtn.addEventListener('click', () => {
    if (stepIndex !== scene.crashStep) return;
    const prevStep = scene.steps[stepIndex];
    fadeText(narration, scene.crashNarration);
    shakeElement(boxA);
    animateValue(balA, prevStep.balances.a, scene.steps[0].balances.a, { duration: 500, format: (v) => `$${v}` });
    balB.textContent = `$${scene.steps[0].balances.b}`;
    paintBadges('A');
    finish();
  });

  nextBtn.addEventListener('click', () => {
    const prevStep = scene.steps[stepIndex];
    stepIndex += 1;
    if (stepIndex >= scene.steps.length) {
      finish();
      return;
    }
    paintStep(scene.steps[stepIndex], prevStep);
  });

  paintStep(scene.steps[0], null);
}

function renderTwoPathsScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const grid = el('div', 'grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6');
  const detail = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[3rem]', 'Click any marker to reveal what it means.');
  const viewed = new Set();
  const totalMarkers = scene.columns.reduce((sum, c) => sum + c.markers.length, 0);

  const controls = el('div', 'flex items-center gap-3');

  function maybeShowContinue() {
    if (viewed.size < totalMarkers || controls.dataset.shown) return;
    controls.dataset.shown = '1';
    const continueBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Continue');
    continueBtn.addEventListener('click', () => {
      container.innerHTML = '';
      const closing = el('div', prefersReducedMotion() ? '' : '');
      container.appendChild(closing);
      closing.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.sharedGround));
      closing.appendChild(el('p', 'text-gray-200 leading-relaxed mb-6', scene.closingNarration));
      const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
      done.addEventListener('click', () => onComplete(scene.xp));
      closing.appendChild(done);
      if (!prefersReducedMotion()) {
        closing.animate(
          [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }],
          { duration: 300, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }
        );
      }
    });
    controls.appendChild(continueBtn);
  }

  scene.columns.forEach((col) => {
    const colEl = el('div', '');
    colEl.appendChild(el('h4', `text-sm font-bold mb-3 text-${col.color}-300`, col.name));
    col.markers.forEach((marker) => {
      const btn = el('button', 'flex items-center gap-2 w-full text-left px-3 py-2 mb-2 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300');
      const dot = el('span', 'w-1.5 h-1.5 rounded-full bg-gray-700 shrink-0 transition-colors duration-300');
      btn.appendChild(dot);
      btn.appendChild(el('span', 'text-xs text-gray-500 mr-1', marker.year));
      btn.appendChild(document.createTextNode(marker.label));
      btn.addEventListener('click', () => {
        fadeText(detail, marker.detail);
        dot.className = 'w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 transition-colors duration-300';
        viewed.add(col.key + ':' + marker.label);
        maybeShowContinue();
      });
      colEl.appendChild(btn);
    });
    grid.appendChild(colEl);
  });

  container.appendChild(grid);
  container.appendChild(detail);
  container.appendChild(controls);
}

function renderScenarioScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let vignetteIndex = 0;
  let earnedXp = 0;

  function paintVignette() {
    body.innerHTML = '';
    const vignette = scene.vignettes[vignetteIndex];
    body.appendChild(el('div', 'text-xs uppercase tracking-wide text-blue-400 mb-2', vignette.category));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', vignette.prompt));

    const optionsWrap = el('div', 'space-y-2 mb-4');
    const feedback = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      vignetteIndex === scene.vignettes.length - 1 ? 'See results' : 'Next situation');

    vignette.options.forEach((option) => {
      const btn = el('button', 'flex w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', option.text);
      btn.addEventListener('click', () => {
        Array.from(optionsWrap.children).forEach((c) => (c.disabled = true));
        btn.className = option.correct
          ? 'flex w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'flex w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        appendFeedbackIcon(btn, option.correct);
        if (option.correct) pulseElement(btn);
        else shakeElement(btn);
        earnedXp += option.correct ? 6 : 2;
        feedback.textContent = option.feedback;
        feedback.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
        if (!prefersReducedMotion()) {
          feedback.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 250, easing: 'ease-out' });
        }
      });
      optionsWrap.appendChild(btn);
    });

    body.appendChild(optionsWrap);
    body.appendChild(feedback);

    nextBtn.addEventListener('click', () => {
      vignetteIndex += 1;
      if (vignetteIndex >= scene.vignettes.length) finish();
      else paintVignette();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You earned ${earnedXp} XP across ${scene.vignettes.length} situations.`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(earnedXp));
    body.appendChild(done);
  }

  paintVignette();
}

function renderQuizScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let qIndex = 0;
  let correctCount = 0;

  function paintQuestion() {
    body.innerHTML = '';
    const q = scene.questions[qIndex];
    body.appendChild(el('div', 'text-xs text-gray-500 mb-2', `Question ${qIndex + 1} of ${scene.questions.length}`));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', q.prompt));

    const choicesWrap = el('div', 'space-y-2 mb-4');
    const explanation = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      qIndex === scene.questions.length - 1 ? 'See results' : 'Next question');

    q.choices.forEach((choiceText, i) => {
      const btn = el('button', 'flex w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', choiceText);
      btn.addEventListener('click', () => {
        Array.from(choicesWrap.children).forEach((c) => (c.disabled = true));
        const isCorrect = i === q.correctIndex;
        btn.className = isCorrect
          ? 'flex w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'flex w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        appendFeedbackIcon(btn, isCorrect);
        if (isCorrect) {
          correctCount += 1;
          pulseElement(btn);
        } else {
          shakeElement(btn);
          const correctBtn = choicesWrap.children[q.correctIndex];
          correctBtn.className = 'flex w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm';
          appendFeedbackIcon(correctBtn, true);
        }
        explanation.textContent = q.explanation;
        explanation.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
        if (!prefersReducedMotion()) {
          explanation.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 250, easing: 'ease-out' });
        }
      });
      choicesWrap.appendChild(btn);
    });

    body.appendChild(choicesWrap);
    body.appendChild(explanation);

    nextBtn.addEventListener('click', () => {
      qIndex += 1;
      if (qIndex >= scene.questions.length) finish();
      else paintQuestion();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    const xp = correctCount * scene.xpPerCorrect;
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You got ${correctCount} of ${scene.questions.length} correct (+${xp} XP).`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(xp));
    body.appendChild(done);
  }

  paintQuestion();
}

const ANIMATION_RENDERERS = {
  'acid-test': renderAcidTestScene,
  'two-paths': renderTwoPathsScene,
};

export function renderScene(container, scene, onComplete) {
  if (scene.type === 'animation') {
    const renderer = ANIMATION_RENDERERS[scene.id];
    if (!renderer) throw new Error(`No animation renderer registered for scene id "${scene.id}"`);
    renderer(container, scene, onComplete);
  } else if (scene.type === 'scenario') {
    renderScenarioScene(container, scene, onComplete);
  } else if (scene.type === 'quiz') {
    renderQuizScene(container, scene, onComplete);
  } else {
    throw new Error(`Unknown scene type "${scene.type}"`);
  }
}

function crossfadeSwap(container, paint) {
  if (prefersReducedMotion() || !container.firstChild) {
    paint();
    return;
  }
  // Rendering the new scene (paint) must happen even if this animation is
  // paused by the browser (backgrounded tab, no compositing), so it's
  // driven by a plain timer rather than the animation's finish event.
  container.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150, easing: 'ease-out' });
  setTimeout(() => {
    paint();
    container.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 220, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' });
  }, 150);
}

export function mountChapterGame(root, { chapterId, scenes, store }) {
  root.innerHTML = '';

  const header = el('div', 'flex items-center justify-between mb-8');
  const xpLabel = el('div', 'text-sm text-gray-400');
  const chapterLabel = el('div', 'text-sm text-gray-400');
  header.appendChild(xpLabel);
  header.appendChild(chapterLabel);
  root.appendChild(header);

  const nav = el('div', 'flex gap-2 mb-8 flex-wrap');
  root.appendChild(nav);

  const sceneContainer = el('div', 'rounded-2xl border border-gray-800 bg-gray-900/40 p-6');
  root.appendChild(sceneContainer);

  let lastXp = store.getTotalXp();

  function navButtonClass(scene, isActive) {
    if (isActive) return 'px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium transition-colors duration-300';
    return store.isSceneComplete(chapterId, scene.id)
      ? 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium transition-colors duration-300'
      : 'px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 text-xs font-medium hover:text-white transition';
  }

  function refreshHeader() {
    const totalXp = store.getTotalXp();
    animateValue(xpLabel, lastXp, totalXp, { duration: 500, format: (v) => `⚡ ${v} XP` });
    lastXp = totalXp;
    const stats = store.getChapterStats(chapterId, scenes.length);
    chapterLabel.textContent = stats.mastered
      ? 'Chapter mastered ✓'
      : `${stats.completedScenes} / ${stats.totalScenes} scenes complete`;
  }

  function selectScene(scene) {
    Array.from(nav.children).forEach((btn) => {
      const btnScene = scenes.find((s) => s.id === btn.dataset.sceneId);
      btn.className = navButtonClass(btnScene, btn.dataset.sceneId === scene.id);
    });
    crossfadeSwap(sceneContainer, () => {
      renderScene(sceneContainer, scene, (xp) => {
        store.awardSceneXp(chapterId, scene.id, xp);
        refreshHeader();
        const navBtn = Array.from(nav.children).find((btn) => btn.dataset.sceneId === scene.id);
        if (navBtn) navBtn.className = 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium transition-colors duration-300';
      });
    });
  }

  scenes.forEach((scene) => {
    const btn = el('button', navButtonClass(scene, false), scene.title);
    btn.dataset.sceneId = scene.id;
    btn.addEventListener('click', () => selectScene(scene));
    nav.appendChild(btn);
  });

  xpLabel.textContent = `⚡ ${lastXp} XP`;
  refreshHeader();
  selectScene(scenes[0]);
}

// Mounts a single scene inline (e.g. embedded in a book chapter page, between
// paragraphs) without the multi-scene nav/header chrome `mountChapterGame`
// uses. Progress is tracked through the same shared `store`, so completing a
// scene here or on the standalone game page updates the same total.
export function mountInlineScene(root, { chapterId, scene, store }) {
  root.innerHTML = '';

  const card = el('div', 'not-prose rounded-2xl border border-gray-800 bg-gray-900/40 p-6 my-8');
  const header = el('div', 'flex items-center justify-between mb-4');
  header.appendChild(el('div', 'text-xs font-semibold text-blue-400 uppercase tracking-wide', `▶ Try it: ${scene.title}`));
  const badge = el('div', 'text-xs text-gray-500');
  header.appendChild(badge);
  card.appendChild(header);

  const sceneContainer = el('div');
  card.appendChild(sceneContainer);
  root.appendChild(card);

  function refreshBadge() {
    if (store.isSceneComplete(chapterId, scene.id)) {
      badge.textContent = '✓ Complete';
      badge.className = 'text-xs text-emerald-400 font-medium';
    } else {
      badge.textContent = scene.xp ? `+${scene.xp} XP` : 'Try it';
      badge.className = 'text-xs text-gray-500';
    }
  }

  refreshBadge();
  renderScene(sceneContainer, scene, (xp) => {
    store.awardSceneXp(chapterId, scene.id, xp);
    refreshBadge();
    pulseElement(badge);
  });
}
