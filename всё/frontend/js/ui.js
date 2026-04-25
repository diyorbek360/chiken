// ui.js — All UI logic: screens, popups, tutorial, animations
class UI {
  constructor() {
    this.currentScreen = "loading";
    this.tutorialStep = 0;
    this.tutorialActive = false;
    this.shopCart = {};   // { item: quantity }
    this._toastQueue = [];
  }

  // ── Screen Management ──────────────────────────────────────
  showScreen(name) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    const el = document.getElementById(`screen-${name}`);
    if (el) el.classList.add("active");
    this.currentScreen = name;

    if (name === "game") this.renderFarmScene();
    if (name === "market") this.renderMarket();
    if (name === "leaders") this.renderLeaders();
    if (name === "settings") this.renderSettings();
  }

  // ── HUD Update ─────────────────────────────────────────────
  updateHUD() {
    const s = game.state;
    if (!s) return;

    // Feed bags
    el("hud-bags").textContent = String(s.feed_bags).padStart(2, "0");

    // Center: super+chickens+eggs
    el("hud-super").textContent = s.super_chickens;
    el("hud-chickens").textContent = s.chickens;
    el("hud-eggs-total").textContent = s.eggs_collected;

    // Day + balance
    el("hud-day-num").textContent = s.game_day;
    el("hud-balance").textContent = `${s.balance_usd.toFixed(2)}$`;

    // Feeder
    const pct = game.getFeederPercent();
    const fillEl = document.querySelector(".feeder-fill");
    if (fillEl) fillEl.style.height = `${pct * 100}%`;

    // Dog house indicator
    const farmEl = document.getElementById("screen-game");
    if (farmEl) {
      farmEl.classList.toggle("has-dog", s.has_dog);
      farmEl.classList.toggle("has-auto-feeder", s.has_auto_feeder);
    }
  }

  // ── Farm Scene ─────────────────────────────────────────────
  renderFarmScene() {
    const s = game.state;
    if (!s) return;

    // Chickens
    const area = document.getElementById("chickens-area");
    if (!area) return;
    area.innerHTML = "";

    const visibleChickens = Math.min(s.chickens, 10);
    const positions = this._getChickenPositions(visibleChickens);

    for (let i = 0; i < visibleChickens; i++) {
      const div = document.createElement("div");
      div.className = "chicken";
      div.style.left = positions[i].x + "%";
      div.style.top = positions[i].y + "%";
      div.style.animationDelay = `${-i * 0.8}s`;
      div.textContent = "🐔";
      area.appendChild(div);
    }

    // Super chickens
    for (let i = 0; i < s.super_chickens; i++) {
      const div = document.createElement("div");
      div.className = "chicken super";
      div.style.left = (30 + i * 20) + "%";
      div.style.top = "40%";
      div.style.animationDelay = `${-i * 1.2}s`;
      div.textContent = "🐓";
      area.appendChild(div);
    }

    // Trader
    const traderEl = document.getElementById("trader-on-farm");
    if (traderEl) traderEl.style.display = s.trader_active ? "block" : "none";

    this.renderEggTray();
    this.updateHUD();
  }

  _getChickenPositions(count) {
    const pos = [
      { x: 30, y: 50 }, { x: 55, y: 60 }, { x: 20, y: 65 },
      { x: 65, y: 45 }, { x: 40, y: 70 }, { x: 10, y: 55 },
      { x: 70, y: 60 }, { x: 50, y: 40 }, { x: 25, y: 75 }, { x: 60, y: 75 },
    ];
    return pos.slice(0, count);
  }

  renderEggTray() {
    const tray = document.getElementById("egg-tray");
    if (!tray) return;
    tray.innerHTML = "";

    const count = Math.min(game.eggCount, 12);
    if (count === 0) {
      const label = document.createElement("span");
      label.className = "tray-empty-label";
      label.textContent = "🐔 Яйца появятся здесь...";
      tray.appendChild(label);
      return;
    }

    for (let i = 0; i < count; i++) {
      const egg = document.createElement("div");
      egg.className = "egg";
      egg.style.animationDelay = `${i * 0.3}s`;
      tray.appendChild(egg);
    }
  }

  animateFeeder() {
    const fill = document.querySelector(".feeder-fill");
    if (!fill) return;
    fill.style.transition = "none";
    fill.style.height = "0%";
    setTimeout(() => {
      fill.style.transition = "height 0.8s ease";
      fill.style.height = "100%";
    }, 50);
  }

  showEggCollectAnimation(eggs, earned) {
    const tray = document.getElementById("egg-tray");
    if (!tray) return;

    const flash = document.createElement("div");
    flash.style.cssText = `
      position:absolute;inset:0;background:rgba(245,197,24,0.5);
      border-radius:12px;pointer-events:none;
      animation:flashOut 0.6s ease forwards;
    `;
    tray.style.position = "relative";
    tray.appendChild(flash);

    const label = document.createElement("div");
    label.style.cssText = `
      position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
      font-family:'Nunito',sans-serif;font-weight:900;font-size:32px;
      color:#F5C518;text-shadow:2px 2px 8px rgba(0,0,0,0.6);
      pointer-events:none;z-index:500;
      animation:floatUp 1.2s ease forwards;
    `;
    label.textContent = `+${earned.toFixed(2)}$ 🥚`;
    document.body.appendChild(label);

    // CSS for these animations
    if (!document.getElementById("anim-style")) {
      const style = document.createElement("style");
      style.id = "anim-style";
      style.textContent = `
        @keyframes flashOut { from{opacity:1} to{opacity:0} }
        @keyframes floatUp { 0%{opacity:1;transform:translate(-50%,-50%)} 100%{opacity:0;transform:translate(-50%,-200%)} }
      `;
      document.head.appendChild(style);
    }

    setTimeout(() => label.remove(), 1200);
    setTimeout(() => flash.remove(), 600);
    this.showToast(`🥚 +${eggs} яиц, +${earned.toFixed(2)}$`, "success");
  }

  // ── Market Screen ──────────────────────────────────────────
  renderMarket() {
    const s = game.state;
    if (!s) return;

    this.shopCart = {};
    this._updateMarketTotal();

    const items = [
      { id: "chicken", emoji: "🐔", nameKey: "chicken_item", owned: false },
      { id: "glove", emoji: "🧤", nameKey: "glove_item", owned: s.has_glove, oneTime: true },
      { id: "super_chicken", emoji: "🐓", nameKey: "super_chicken_item", owned: false },
      { id: "dog", emoji: "🐕", nameKey: "dog_item", owned: s.has_dog, oneTime: true },
      { id: "feed", emoji: "🌾", nameKey: "feed_item", owned: false },
      { id: "auto_feeder", emoji: "⚙️", nameKey: "auto_feeder_item", owned: s.has_auto_feeder, oneTime: true },
    ];

    const grid = document.getElementById("shop-grid");
    if (!grid) return;
    grid.innerHTML = "";

    items.forEach(item => {
      const price = this._getItemPrice(item.id);
      const card = document.createElement("div");
      card.className = `shop-item${item.owned ? " owned" : ""}`;
      card.id = `shop-item-${item.id}`;

      // Count badge
      const count = document.createElement("div");
      count.className = "shop-item-count";
      count.id = `shop-count-${item.id}`;
      count.textContent = this._getItemCurrentCount(item.id, s);

      // Price badge
      const badge = document.createElement("div");
      badge.className = "shop-price-badge";
      badge.textContent = price;

      // Emoji
      const emoji = document.createElement("span");
      emoji.className = "shop-item-emoji";
      emoji.textContent = item.emoji;

      // Name
      const name = document.createElement("div");
      name.className = "shop-item-name";
      name.textContent = i18n.t(item.nameKey);

      card.appendChild(count);
      card.appendChild(badge);
      card.appendChild(emoji);
      card.appendChild(name);

      if (item.owned) {
        const owned = document.createElement("div");
        owned.className = "shop-owned-badge";
        owned.textContent = i18n.t("already_owned");
        card.appendChild(owned);
      } else {
        const controls = document.createElement("div");
        controls.className = "shop-item-controls";

        const minus = document.createElement("button");
        minus.className = "shop-qty-btn";
        minus.textContent = "−";
        minus.onclick = (e) => { e.stopPropagation(); this._changeQty(item.id, -1); };

        const qty = document.createElement("div");
        qty.className = "shop-qty-val";
        qty.id = `shop-qty-${item.id}`;
        qty.textContent = "0";

        const plus = document.createElement("button");
        plus.className = "shop-qty-btn";
        plus.textContent = "+";
        plus.onclick = (e) => { e.stopPropagation(); this._changeQty(item.id, 1); };

        controls.appendChild(minus);
        controls.appendChild(qty);
        controls.appendChild(plus);
        card.appendChild(controls);
      }

      // Click for info popup
      card.addEventListener("click", () => this.showItemInfoPopup(item));
      grid.appendChild(card);
    });
  }

  _getItemPrice(id) {
    const p = game.prices;
    if (!p) return "?";
    const map = {
      chicken: `${p.chicken?.usd || 1}$`,
      feed: `${p.feed?.usd || 0.18}$`,
      glove: `${p.glove?.usd || 2}$`,
      dog: `${p.dog?.usd || 5}$`,
      super_chicken: `${p.super_chicken?.usd || 3}$`,
      auto_feeder: `${p.auto_feeder?.percent || 3}%`,
    };
    return map[id] || "?";
  }

  _getItemCurrentCount(id, s) {
    const map = {
      chicken: s.chickens,
      feed: s.feed_bags,
      glove: s.has_glove ? 1 : 0,
      dog: s.has_dog ? 1 : 0,
      super_chicken: s.super_chickens,
      auto_feeder: s.has_auto_feeder ? 1 : 0,
    };
    return map[id] ?? 0;
  }

  _changeQty(itemId, delta) {
    this.shopCart[itemId] = Math.max(0, (this.shopCart[itemId] || 0) + delta);
    const el = document.getElementById(`shop-qty-${itemId}`);
    if (el) el.textContent = this.shopCart[itemId];
    this._updateMarketTotal();
  }

  _updateMarketTotal() {
    const p = game.prices || {};
    const priceMap = {
      chicken: p.chicken?.usd || 1,
      feed: p.feed?.usd || 0.18,
      glove: p.glove?.usd || 2,
      dog: p.dog?.usd || 5,
      super_chicken: p.super_chicken?.usd || 3,
      auto_feeder: p.auto_feeder?.percent || 1,
    };

    let total = 0;
    let summary = [];
    Object.entries(this.shopCart).forEach(([item, qty]) => {
      if (qty > 0) {
        const cost = priceMap[item] * qty;
        total += cost;
        summary.push(`${qty}x ${i18n.t(item + "_item")}: ${cost.toFixed(2)}$`);
      }
    });

    const totalArea = document.getElementById("market-total-area");
    if (totalArea) {
      totalArea.innerHTML = summary.length
        ? `${summary.join("<br>")}<div class="market-total-row"><span>${i18n.t("total_label")}</span><span>${total.toFixed(2)}$</span></div>`
        : `<span style="color:#aaa;font-size:13px;">Выберите товары...</span>`;
    }
  }

  async purchaseCart() {
    const hasItems = Object.values(this.shopCart).some(q => q > 0);
    if (!hasItems) { this.showToast("Добавьте товары в корзину", "warning"); return; }

    let allOk = true;
    for (const [item, qty] of Object.entries(this.shopCart)) {
      if (qty <= 0) continue;
      const res = await game.buyItem(item, qty);
      if (!res?.success) { allOk = false; break; }
    }

    if (allOk) {
      this.showToast("✅ Покупка совершена!", "success");
      this.shopCart = {};
      this.renderMarket();
      // Market tutorial step
      if (game.state && !game.state.tutorial_market_done) {
        setTimeout(() => api.completeMarketTutorial(), 500);
      }
    }
  }

  showItemInfoPopup(item) {
    const descriptions = {
      chicken: "Дополнительная курица несёт больше яиц! Каждая курица приносит 0.20$ в день.",
      glove: "Перчатка вора позволяет красть 10% суточного урожая другого игрока. Один раз у каждого!",
      super_chicken: "Суперкурица в цепях! Несёт яиц в 2 раза больше обычной. 🏆",
      dog: "Сторожевой пёс защищает ваши яйца от воров! Никто не сможет ничего украсть.",
      feed: "Мешок корма для ваших куриц. Одна порция на 24 часа для каждой курицы.",
      auto_feeder: "Автоматическая кормушка! Кормит куриц сама, пока есть запасы корма. 🤖",
    };

    const popup = document.getElementById("popup-item-info");
    const title = document.getElementById("popup-item-info-title");
    const body = document.getElementById("popup-item-info-body");
    const emoji = document.getElementById("popup-item-info-emoji");

    if (popup && title && body) {
      title.textContent = i18n.t(item.nameKey);
      body.textContent = descriptions[item.id] || "";
      emoji.textContent = item.emoji;
      popup.classList.remove("hidden");
    }
  }

  // ── Leaders ────────────────────────────────────────────────
  async renderLeaders() {
    const listEl = document.getElementById("leaders-list");
    const playerListEl = document.getElementById("players-list");
    if (!listEl) return;

    listEl.innerHTML = "<div style='text-align:center;color:#888;padding:20px;'>Загрузка...</div>";

    try {
      const data = await api.getLeaderboard();
      game.leaderboard = data.leaders;
      this._renderLeaderRows(listEl, data.leaders.slice(0, 3), true);
      this._renderLeaderRows(playerListEl, data.leaders, false, game.state?.id);
    } catch (e) {
      listEl.innerHTML = "<div style='text-align:center;color:#888;padding:20px;'>Не удалось загрузить</div>";
    }
  }

  _renderLeaderRows(container, leaders, isTop, myId = null) {
    if (!container) return;
    container.innerHTML = "";
    leaders.forEach((p, i) => {
      const row = document.createElement("div");
      row.className = "leader-row";
      if (i < 3) row.classList.add("top-3");
      if (p.id === myId) row.classList.add("leader-me");

      const medals = ["🥇", "🥈", "🥉"];
      row.innerHTML = `
        <span class="leader-rank">${i < 3 ? medals[i] : `${p.rank}.`}</span>
        <span class="leader-name">${p.nickname}</span>
        <span class="leader-score">${p.balance_usd.toFixed(2)}$</span>
      `;
      row.addEventListener("click", () => this.showPlayerFarm(p));
      container.appendChild(row);
    });
  }

  async showPlayerFarm(player) {
    try {
      const data = await api.getPlayerFarm(player.id);
      const popup = document.getElementById("popup-player-farm");
      el("pfarm-name").textContent = data.nickname;
      el("pfarm-chickens").textContent = `${i18n.t("chickens_label")} ${data.chickens}`;
      el("pfarm-day").textContent = `${i18n.t("day_label")} ${data.game_day}`;
      el("pfarm-dog").textContent = data.has_dog ? "🐕 Охраняется собакой" : "";

      const stealBtn = document.getElementById("pfarm-steal-btn");
      if (stealBtn) {
        if (data.already_stolen_today) {
          stealBtn.textContent = i18n.t("already_stolen");
          stealBtn.disabled = true;
        } else {
          stealBtn.textContent = i18n.t("steal_btn");
          stealBtn.disabled = false;
          stealBtn.onclick = () => this._doSteal(player.id, data);
        }
      }
      popup.classList.remove("hidden");
    } catch (e) {
      this.showToast("Не удалось загрузить ферму", "error");
    }
  }

  async _doSteal(playerId, data) {
    if (!game.state.has_glove) {
      this.showPopup({
        emoji: "🧤",
        title: "Нет перчатки!",
        body: i18n.t("no_glove_popup"),
        btns: [
          { label: i18n.t("go_to_market"), cls: "popup-btn-primary", action: () => { this.closeAllPopups(); this.showScreen("market"); } },
          { label: i18n.t("close_btn"), cls: "popup-btn-secondary", action: () => this.closeAllPopups() },
        ]
      });
      return;
    }

    if (data.has_dog) {
      this.showToast(i18n.t("dog_protection"), "warning");
      return;
    }

    const res = await game.steal(playerId);
    if (res.success) {
      this.showToast(`🧤 Украдено ${res.amount_usd?.toFixed(2)}$!`, "success");
      game.state.balance_usd += res.amount_usd || 0;
      this.updateHUD();
    } else {
      const msgs = {
        dog_protection: i18n.t("dog_protection"),
        already_stolen_today: i18n.t("already_stolen"),
        no_glove: i18n.t("no_glove_popup"),
      };
      this.showToast(msgs[res.reason] || "Не удалось украсть", "error");
    }
    document.getElementById("popup-player-farm")?.classList.add("hidden");
  }

  // ── Settings ───────────────────────────────────────────────
  async renderSettings() {
    const s = game.state;
    if (!s) return;

    const nick = document.getElementById("settings-nickname");
    if (nick) nick.value = s.nickname || "";

    const wallet = document.getElementById("settings-wallet");
    if (wallet) wallet.value = s.ton_wallet || "";

    el("settings-balance")?.textContent && (el("settings-balance").textContent = `${s.balance_usd.toFixed(2)}$`);

    // Referrals
    try {
      const refData = await api.getReferrals();
      const link = document.getElementById("settings-referral-link");
      if (link) link.textContent = refData.referral_link || "";
      const count = document.getElementById("settings-referral-count");
      if (count) count.textContent = refData.referred_count || 0;
    } catch (e) {}

    // Withdrawal history
    try {
      const hist = await api.getWithdrawHistory();
      this._renderWithdrawHistory(hist.history);
    } catch (e) {}

    // Lang
    const langSel = document.getElementById("settings-lang");
    if (langSel) langSel.value = s.language || "ru";
  }

  _renderWithdrawHistory(history) {
    const container = document.getElementById("withdraw-history");
    if (!container) return;
    container.innerHTML = "";
    if (!history.length) {
      container.innerHTML = "<div style='color:#aaa;font-size:13px;text-align:center;padding:10px;'>История пуста</div>";
      return;
    }
    history.forEach(w => {
      const row = document.createElement("div");
      row.className = "history-row";
      const date = new Date(w.date).toLocaleDateString("ru-RU");
      row.innerHTML = `
        <span class="history-date">${date}</span>
        <span class="history-amount">${w.amount.toFixed(2)}$</span>
        <span class="history-status status-${w.status}">${w.status}</span>
      `;
      container.appendChild(row);
    });
  }

  async saveNickname() {
    const input = document.getElementById("settings-nickname");
    if (!input || !input.value.trim()) return;
    try {
      await api.updateNickname(input.value.trim());
      game.state.nickname = input.value.trim();
      this.showToast("✅ Ник сохранён!", "success");
    } catch (e) { this.showToast("Ошибка сохранения", "error"); }
  }

  async saveWallet() {
    const input = document.getElementById("settings-wallet");
    if (!input || !input.value.trim()) return;
    try {
      await api.updateWallet(input.value.trim());
      game.state.ton_wallet = input.value.trim();
      this.showToast(i18n.t("wallet_saved"), "success");
    } catch (e) { this.showToast("Ошибка сохранения", "error"); }
  }

  async requestWithdraw() {
    const s = game.state;
    if (!s.ton_wallet) {
      this.showToast(i18n.t("no_wallet"), "warning");
      return;
    }
    if (s.balance_usd <= 0) {
      this.showToast("Нет средств для вывода", "warning");
      return;
    }
    this.showPopup({
      emoji: "💰",
      title: "Вывод средств",
      body: `Вывести ${s.balance_usd.toFixed(2)}$\nна кошелёк ${s.ton_wallet.slice(0, 12)}...?`,
      btns: [
        {
          label: i18n.t("yes_btn"), cls: "popup-btn-primary",
          action: async () => {
            try {
              await api.requestWithdrawal(s.balance_usd);
              this.showToast(i18n.t("withdraw_pending"), "success");
              game.state.balance_usd = 0;
              this.updateHUD();
              this.renderSettings();
            } catch (e) { this.showToast("Ошибка запроса", "error"); }
            this.closeAllPopups();
          }
        },
        { label: i18n.t("no_btn"), cls: "popup-btn-secondary", action: () => this.closeAllPopups() },
      ]
    });
  }

  copyReferralLink() {
    const link = document.getElementById("settings-referral-link")?.textContent;
    if (!link) return;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(link);
      this.showToast("✅ Ссылка скопирована!", "success");
    }
    // Telegram share
    if (window.Telegram?.WebApp) {
      const msg = i18n.t("invite_msg") + link;
      window.Telegram.WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(msg)}`);
    }
  }

  async changeLang(lang) {
    i18n.setLang(lang);
    game.state.language = lang;
    try { await api.updateLanguage(lang); } catch (e) {}
    // Re-render current screen
    this.renderFarmScene();
    this.renderNavButtons();
  }

  // ── Tutorial ───────────────────────────────────────────────
  startTutorial() {
    this.tutorialStep = 0;
    this.tutorialActive = true;
    this._showTutorialStep(0);
  }

  _showTutorialStep(step) {
    const steps = [
      { text: i18n.t("tutorial_1"), highlight: ".feeder" },
      { text: i18n.t("tutorial_2"), highlight: ".feeder" },
      { text: i18n.t("tutorial_3"), highlight: ".hud-bag" },
      { text: i18n.t("tutorial_4"), highlight: ".market-building" },
      { text: i18n.t("tutorial_5"), highlight: ".dog-house" },
      { text: i18n.t("tutorial_6"), highlight: ".hud-day" },
    ];

    if (step >= steps.length) {
      this._endTutorial();
      return;
    }

    const s = steps[step];
    const speech = document.getElementById("tutorial-speech");
    if (speech) {
      speech.textContent = s.text;
      speech.classList.remove("hidden");
    }

    // Highlight element
    this._highlightElement(s.highlight);

    // Hand pointer
    const hand = document.getElementById("tutorial-hand");
    const targetEl = document.querySelector(s.highlight);
    if (hand && targetEl) {
      const rect = targetEl.getBoundingClientRect();
      hand.style.left = (rect.right - 20) + "px";
      hand.style.top = (rect.bottom - 20) + "px";
      hand.style.display = "block";
    }

    document.getElementById("tutorial-overlay").style.display = "block";
  }

  _highlightElement(selector) {
    const highlight = document.getElementById("tutorial-highlight");
    const targetEl = document.querySelector(selector);
    if (!highlight || !targetEl) return;

    const rect = targetEl.getBoundingClientRect();
    highlight.style.left = (rect.left - 8) + "px";
    highlight.style.top = (rect.top - 8) + "px";
    highlight.style.width = (rect.width + 16) + "px";
    highlight.style.height = (rect.height + 16) + "px";
  }

  advanceTutorial() {
    this.tutorialStep++;
    this._showTutorialStep(this.tutorialStep);
  }

  _endTutorial() {
    this.tutorialActive = false;
    document.getElementById("tutorial-overlay").style.display = "none";
    document.getElementById("tutorial-hand").style.display = "none";
    try { api.completeTutorial(); } catch (e) {}
    if (game.state) game.state.tutorial_completed = true;
    // Show trader hint if applicable
    if (game.state?.trader_active) {
      this.showTraderPopup();
    }
  }

  // ── Trader ─────────────────────────────────────────────────
  showTraderPopup() {
    const s = game.state;
    if (!s) return;
    const popup = document.getElementById("popup-trader");
    if (!popup) return;

    const price = (game.prices?.chicken?.usd || 1) * (1 - 0.20);
    el("trader-chicken-price")?.textContent && (el("trader-chicken-price").textContent = `${price.toFixed(2)}$`);
    el("trader-withdraw-amount")?.textContent && (el("trader-withdraw-amount").textContent = `${s.balance_usd.toFixed(2)}$`);

    popup.classList.remove("hidden");
  }

  async traderBuyChicken() {
    const res = await game.buyItem("chicken", 1);
    if (res?.success) {
      document.getElementById("popup-trader")?.classList.add("hidden");
      this.showToast("🐔 Куплена курица со скидкой!", "success");
      this.renderFarmScene();
    }
  }

  async traderWithdraw() {
    document.getElementById("popup-trader")?.classList.add("hidden");
    this.showScreen("settings");
    setTimeout(() => this.requestWithdraw(), 300);
  }

  // ── Generic Popup ──────────────────────────────────────────
  showPopup({ emoji, title, body, btns }) {
    const overlay = document.getElementById("popup-generic");
    el("popup-generic-emoji").textContent = emoji || "";
    el("popup-generic-title").textContent = title || "";
    el("popup-generic-body").textContent = body || "";

    const btnsEl = document.getElementById("popup-generic-btns");
    btnsEl.innerHTML = "";
    (btns || []).forEach(b => {
      const btn = document.createElement("button");
      btn.className = `popup-btn ${b.cls || "popup-btn-secondary"}`;
      btn.textContent = b.label;
      btn.onclick = b.action;
      btnsEl.appendChild(btn);
    });

    overlay.classList.remove("hidden");
  }

  showChickenDeadPopup() {
    this.showPopup({
      emoji: "💀",
      title: i18n.t("chicken_died_title"),
      body: i18n.t("chicken_died_body"),
      btns: [{
        label: i18n.t("restart_btn"),
        cls: "popup-btn-primary",
        action: () => { this.closeAllPopups(); this.renderFarmScene(); }
      }]
    });
  }

  closeAllPopups() {
    document.querySelectorAll(".popup-overlay").forEach(p => p.classList.add("hidden"));
  }

  // ── Toast ──────────────────────────────────────────────────
  showToast(msg, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  renderNavButtons() {
    const labels = [
      { id: "nav-market-label", key: "market_btn" },
      { id: "nav-leaders-label", key: "leaders_title" },
      { id: "nav-settings-label", key: "settings_title" },
    ];
    labels.forEach(l => {
      const el = document.getElementById(l.id);
      if (el) el.textContent = i18n.t(l.key);
    });
  }
}

// Helper
function el(id) { return document.getElementById(id); }

window.ui = new UI();
