// Pure, storage-agnostic progress tracking for the DBA Handbook interactive game.

export const STORAGE_KEY = 'dba-handbook-progress';

export function parseProgress(raw) {
  if (typeof raw !== 'string') return { xp: 0, chapters: {} };
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return { xp: 0, chapters: {} };
    return {
      xp: typeof parsed.xp === 'number' ? parsed.xp : 0,
      chapters: parsed.chapters && typeof parsed.chapters === 'object' ? parsed.chapters : {},
    };
  } catch {
    return { xp: 0, chapters: {} };
  }
}

export function serializeProgress(progress) {
  return JSON.stringify(progress);
}

export function createStorageAdapter(storageLike) {
  const probeKey = '__dba_handbook_probe__';
  let usable = false;
  try {
    storageLike.setItem(probeKey, '1');
    storageLike.removeItem(probeKey);
    usable = true;
  } catch {
    usable = false;
  }

  if (usable) {
    return {
      read() {
        try {
          return storageLike.getItem(STORAGE_KEY);
        } catch {
          return null;
        }
      },
      write(str) {
        try {
          storageLike.setItem(STORAGE_KEY, str);
          return true;
        } catch {
          return false;
        }
      },
    };
  }

  let memory = null;
  return {
    read() {
      return memory;
    },
    write(str) {
      memory = str;
      return true;
    },
  };
}

export function createProgressStore(storageLike) {
  const adapter = createStorageAdapter(storageLike);
  let progress = parseProgress(adapter.read());

  function persist() {
    adapter.write(serializeProgress(progress));
  }

  return {
    getProgress() {
      return JSON.parse(JSON.stringify(progress));
    },

    isSceneComplete(chapterId, sceneId) {
      return Boolean(progress.chapters[chapterId] && progress.chapters[chapterId][sceneId] !== undefined);
    },

    awardSceneXp(chapterId, sceneId, xp) {
      if (!progress.chapters[chapterId]) progress.chapters[chapterId] = {};
      if (progress.chapters[chapterId][sceneId] !== undefined) {
        return this.getProgress();
      }
      progress.chapters[chapterId][sceneId] = xp;
      progress.xp += xp;
      persist();
      return this.getProgress();
    },

    getChapterStats(chapterId, totalScenes) {
      const scenes = progress.chapters[chapterId] || {};
      const completedScenes = Object.keys(scenes).length;
      return {
        completedScenes,
        totalScenes,
        mastered: completedScenes >= totalScenes,
      };
    },

    getTotalXp() {
      return progress.xp;
    },

    getChaptersMasteredCount(chapterTotals) {
      return Object.entries(chapterTotals).filter(([chapterId, totalScenes]) => {
        return this.getChapterStats(chapterId, totalScenes).mastered;
      }).length;
    },
  };
}
