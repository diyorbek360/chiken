// game.js — Game state & core logic (client-side)
class Game {
  constructor() {
    this.state = null;       // user data from backend
    this.eggCount = 0;       // eggs in tray (visual)
    this.prices = null;
    this.leaderboard = null;
    this.referrals = null;
    this._tickInterval = null;
    this._eggInterval = null;
  }

  // ── Initialise ─────────────────────────────────────────────
  async init(telegramId, username, language, referralCode) {
    try {
      const data = await api.initPlayer(telegramId, username, language, referralCode);
      this.state = data.user;
      this.prices = await api.getPrices();

      // Sync eggs visually based on time
      this._syncEggCount();

      // Start tick
      this._startTick();

      return { user: data.user, isNew: data.is_new, chickenAlive: data.chicken_alive };
    } catch (e) {
      console.error("Game init failed:", e);
      // Fallback offline demo mode
      this._loadOfflineDemo();
      return { user: this.state, isNew: true, chickenAlive: { alive: true, hours_remaining: 24 } };
    }
  }

  _loadOfflineDemo() {
    this.state = {
      id: 1,
      telegram_id: 0,
      nickname: "Demo Player",
      language: i18n.lang,
      game_day: 1,
      chickens: 1,
      super_chickens: 0,
      feed_bags: 0,
      eggs_collected: 0,
      balance_usd: 0,
      balance_ton: 0,
      has_glove: false,
      has_dog: false,
      has_auto_feeder: false,
      feeder_level: 0,
      last_fed_at: null,
      ton_wallet: null,
      referral_code: "DEMO1234",
      tutorial_completed: false,
      tutorial_market_done: false,
      trader_active: false,
      days_until_trader: 9,
    };
    this.prices = {
      chicken: { usd: 1.0 },
      feed: { usd: 0.18 },
      glove: { usd: 2.0 },
      dog: { usd: 5.0 },
      super_chicken: { usd: 3.0 },
      auto_feeder: { percent: 3 },
    };
  }

  // ── Sync egg count visually ─────────────────────────────────
  _syncEggCount() {
    const s = this.state;
    if (!s.last_fed_at) { this.eggCount = 0; return; }
    const lastFed = new Date(s.last_fed_at);
    const hours = (Date.now() - lastFed) / 3600000;
    const totalChickens = s.chickens + s.super_chickens * 2;
    this.eggCount = Math.min(Math.floor((hours / 24) * totalChickens * 5), totalChickens * 10);
  }

  // ── Periodic tick (every minute) ───────────────────────────
  _startTick() {
    if (this._tickInterval) clearInterval(this._tickInterval);
    this._tickInterval = setInterval(() => this._tick(), 60000);
    // Drop an egg every few seconds visually
    this._eggInterval = setInterval(() => this._dropEggVisual(), 8000);
  }

  async _tick() {
    try {
      const data = await api.getMe();
      this.state = data.user;
      const alive = data.chicken_alive;

      if (!alive.alive && alive.died) {
        ui.showChickenDeadPopup();
        return;
      }
      if (alive.warning) {
        ui.showToast(i18n.t("death_warning"), "warning");
      }
      if (this.state.feed_bags <= 1) {
        ui.showToast(i18n.t("low_feed_warning"), "warning");
      }
      this._syncEggCount();
      ui.updateHUD();
    } catch (e) { /* offline — silent */ }
  }

  _dropEggVisual() {
    const s = this.state;
    if (!s || !s.last_fed_at) return;
    const total = s.chickens + s.super_chickens * 2;
    if (total <= 0) return;
    this.eggCount = Math.min(this.eggCount + 1, total * 10);
    ui.renderEggTray();
  }

  // ── Actions ────────────────────────────────────────────────
  async feedChickens() {
    try {
      const res = await api.feed();
      if (res.success) {
        this.state.feed_bags = res.remaining_bags;
        this.state.feeder_level = res.feeder_level;
        this.state.last_fed_at = new Date().toISOString();
        this.eggCount = 0;
        ui.updateHUD();
        ui.animateFeeder();
        ui.showToast("🌾 Курица накормлена!", "success");
        return res;
      } else {
        if (res.error === "no_feed") {
          ui.showToast(i18n.t("no_feed_error"), "error");
        }
        return res;
      }
    } catch (e) {
      // offline demo
      if (this.state.feed_bags > 0) {
        this.state.feed_bags--;
        this.state.feeder_level = 1.0;
        this.state.last_fed_at = new Date().toISOString();
        this.eggCount = 0;
        ui.updateHUD();
        ui.animateFeeder();
      } else {
        ui.showToast(i18n.t("no_feed_error"), "error");
      }
    }
  }

  async collectEggs() {
    if (this.eggCount === 0) {
      ui.showToast("Пока яиц нет... 🐔", "warning");
      return;
    }
    try {
      const res = await api.collect();
      if (res.success && res.eggs > 0) {
        this.state.balance_usd += res.earned;
        this.state.eggs_collected += res.eggs;
        this.eggCount = 0;
        ui.renderEggTray();
        ui.updateHUD();
        ui.showEggCollectAnimation(res.eggs, res.earned);
      }
    } catch (e) {
      // offline demo
      const earned = this.eggCount * 0.20;
      this.state.balance_usd += earned;
      const eggs = this.eggCount;
      this.eggCount = 0;
      ui.renderEggTray();
      ui.updateHUD();
      ui.showEggCollectAnimation(eggs, earned);
    }
  }

  async buyItem(item, quantity = 1) {
    try {
      const res = await api.buyItem(item, quantity);
      if (res.success) {
        // Update local state
        this.state.balance_usd -= res.cost;
        if (item === "chicken") this.state.chickens += quantity;
        if (item === "feed") this.state.feed_bags += quantity;
        if (item === "glove") this.state.has_glove = true;
        if (item === "dog") this.state.has_dog = true;
        if (item === "auto_feeder") this.state.has_auto_feeder = true;
        if (item === "super_chicken") this.state.super_chickens += quantity;
        ui.updateHUD();
        ui.renderFarmScene();
        return { success: true };
      } else {
        if (res.error === "insufficient_balance") {
          ui.showToast(i18n.t("insufficient_balance"), "error");
        } else if (res.error === "already_owned") {
          ui.showToast(i18n.t("already_owned"), "warning");
        }
        return res;
      }
    } catch (e) {
      // Offline: just update state directly
      const priceMap = { chicken: 1.0, feed: 0.18, glove: 2.0, dog: 5.0, super_chicken: 3.0, auto_feeder: 1.0 };
      const cost = (priceMap[item] || 1) * quantity;
      if (this.state.balance_usd < cost) {
        ui.showToast(i18n.t("insufficient_balance"), "error");
        return { success: false };
      }
      this.state.balance_usd -= cost;
      if (item === "chicken") this.state.chickens += quantity;
      if (item === "feed") this.state.feed_bags += quantity;
      if (item === "glove") this.state.has_glove = true;
      if (item === "dog") this.state.has_dog = true;
      if (item === "auto_feeder") this.state.has_auto_feeder = true;
      ui.updateHUD();
      ui.renderFarmScene();
      return { success: true };
    }
  }

  async steal(victimId) {
    try {
      return await api.steal(victimId);
    } catch (e) {
      return { success: false, reason: "network_error" };
    }
  }

  getFeederPercent() {
    const s = this.state;
    if (!s || !s.last_fed_at) return 0;
    const lastFed = new Date(s.last_fed_at);
    const hours = (Date.now() - lastFed) / 3600000;
    return Math.max(0, 1 - hours / 24);
  }

  getHoursUntilDeath() {
    const s = this.state;
    if (!s || !s.last_fed_at) return 0;
    const lastFed = new Date(s.last_fed_at);
    const hours = (Date.now() - lastFed) / 3600000;
    return Math.max(0, 24 - hours);
  }

  destroy() {
    clearInterval(this._tickInterval);
    clearInterval(this._eggInterval);
  }
}

window.game = new Game();
