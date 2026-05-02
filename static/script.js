const ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"];

const championSearch = document.getElementById("championSearch");
const suggestionList = document.getElementById("suggestionList");
const clearChampion = document.getElementById("clearChampion");
const searchChampionAvatar = document.getElementById("searchChampionAvatar");
const searchAvatarWrap = document.getElementById("searchAvatarWrap");

const resultsSection = document.getElementById("resultsSection");
const selectedAvatarWrap = document.getElementById("selectedAvatarWrap");
const selectedChampionAvatar = document.getElementById("selectedChampionAvatar");
const selectedChampionName = document.getElementById("selectedChampionName");
const selectedChampionMeta = document.getElementById("selectedChampionMeta");
const roleList = document.getElementById("roleList");
const detailPanel = document.getElementById("detailPanel");

const counterSection = document.getElementById("counterSection");
const counterTitle = document.getElementById("counterTitle");
const counterSubtitle = document.getElementById("counterSubtitle");
const pickAgainstList = document.getElementById("pickAgainstList");
const avoidIntoList = document.getElementById("avoidIntoList");

let championCatalog = [];
let championByName = new Map();
let currentChampion = null;
let currentRoleStats = [];
let activeRole = null;
let _isSelecting = false;

function openSuggestions() {
	suggestionList.hidden = false;
	suggestionList.classList.add("show");
}

function closeSuggestions() {
	suggestionList.classList.remove("show");
}

function normalizeName(name) {
	return name.trim().toLowerCase();
}

async function fetchDataDragonChampions() {
	const versionsRes = await fetch("https://ddragon.leagueoflegends.com/api/versions.json");
	const versions = await versionsRes.json();
	const version = versions[0];

	const dataRes = await fetch(
		`https://ddragon.leagueoflegends.com/cdn/${version}/data/en_US/champion.json`,
	);
	const payload = await dataRes.json();
	const data = payload.data || {};

	championCatalog = Object.values(data)
		.map((champ) => ({
			champion_name: champ.name,
			image_url: `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${champ.image.full}`,
		}))
		.sort((a, b) => a.champion_name.localeCompare(b.champion_name));

	championByName = new Map(
		championCatalog.map((champ) => [normalizeName(champ.champion_name), champ]),
	);
}

function getChampionImageUrl(name) {
	const found = championByName.get(normalizeName(name));
	if (found) {
		return found.image_url;
	}
	return "https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/Aatrox.png";
}

function setSearchAvatar(url = "") {
	if (url) {
		searchChampionAvatar.src = url;
		searchAvatarWrap.classList.remove("placeholder");
		return;
	}
	searchChampionAvatar.removeAttribute("src");
	searchAvatarWrap.classList.add("placeholder");
}

function setSelectedAvatar(url = "") {
	if (url) {
		selectedChampionAvatar.src = url;
		selectedAvatarWrap.classList.remove("placeholder");
		return;
	}
	selectedChampionAvatar.removeAttribute("src");
	selectedAvatarWrap.classList.add("placeholder");
}

function renderSuggestions(matches) {
	suggestionList.innerHTML = "";
	if (!matches.length) {
		closeSuggestions();
		return;
	}

	const fragment = document.createDocumentFragment();
	for (const champion of matches) {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "suggestion-item";
		button.innerHTML = `
			<img class="chip-avatar" src="${champion.image_url}" alt="${champion.champion_name}">
			<span>${champion.champion_name}</span>
		`;
		// Use pointerdown so the selection runs before blur/input events
		button.addEventListener("pointerdown", (ev) => {
			ev.preventDefault();
			_isSelecting = true;
			championSearch.value = champion.champion_name;
			closeSuggestions();
			selectChampion(champion.champion_name);
			try { championSearch.blur(); } catch (e) {}
			setTimeout(() => (_isSelecting = false), 50);
		});
		fragment.appendChild(button);
	}

	suggestionList.appendChild(fragment);
	openSuggestions();
}

async function fetchRoleStats(championName) {
	const responses = await Promise.all(
		ROLES.map(async (role) => {
			const response = await fetch(
				`/champ_stats?champion=${encodeURIComponent(championName)}&role=${encodeURIComponent(role)}`,
			);
			const payload = await response.json();
			if (!payload.error) {
				return payload;
			}
			return null;
		}),
	);

	return responses.filter(Boolean);
}

function renderRoleButtons(statsRows) {
	roleList.innerHTML = "";
	const fragment = document.createDocumentFragment();

	for (const row of statsRows) {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "role-pill";
		button.dataset.role = row.role;
		button.innerHTML = `
			<div class="role-head">${row.role}</div>
			<div class="role-sub">Win ${Number(row.winrate).toFixed(2)}%</div>
		`;
		button.addEventListener("click", () => {
			setActiveRole(row.role);
		});
		fragment.appendChild(button);
	}

	roleList.appendChild(fragment);
}

function setActiveRole(role) {
	activeRole = role;
	for (const element of roleList.querySelectorAll(".role-pill")) {
		element.classList.toggle("active", element.dataset.role === role);
	}

	const roleStats = currentRoleStats.find((entry) => entry.role === role);
	if (roleStats) {
		renderDetail(roleStats);
		void loadCounters(roleStats.champion_name, roleStats.role);
	}
}

function renderDetail(roleStats) {
	detailPanel.innerHTML = `
		<div class="detail-head">
			<img class="detail-avatar" src="${getChampionImageUrl(roleStats.champion_name)}" alt="${roleStats.champion_name}">
			<div>
				<h3>${roleStats.champion_name}</h3>
				<p>${roleStats.role}</p>
			</div>
		</div>
		<div class="stat-grid">
			<div class="stat-card">
				<span>Tier</span>
				<strong>${roleStats.tier_number}</strong>
			</div>
			<div class="stat-card">
				<span>Win Rate</span>
				<strong>${Number(roleStats.winrate).toFixed(2)}%</strong>
			</div>
			<div class="stat-card">
				<span>Pick Rate</span>
				<strong>${Number(roleStats.pickrate).toFixed(2)}%</strong>
			</div>
		</div>
	`;
}

function renderCounterList(container, rows, emptyMessage) {
	container.innerHTML = "";
	if (!rows.length) {
		container.innerHTML = `<p class="empty-state">${emptyMessage}</p>`;
		return;
	}

	const fragment = document.createDocumentFragment();
	for (const row of rows) {
		const card = document.createElement("div");
		card.className = "champ-row";
		card.innerHTML = `
			<div class="champ-row-left">
				<img class="champ-row-avatar" src="${getChampionImageUrl(row.counter_champion)}" alt="${row.counter_champion}">
				<div>
					<div class="champ-row-name">${row.counter_champion}</div>
					<div class="champ-row-sub">Rank #${row.rank}</div>
				</div>
			</div>
			<div class="champ-row-right">${Number(row.matchup_winrate).toFixed(2)}%</div>
		`;
		fragment.appendChild(card);
	}
	container.appendChild(fragment);
}

async function loadCounters(championName, role) {
	const [strongResponse, weakResponse] = await Promise.all([
		fetch(
			`/counters?champion=${encodeURIComponent(championName)}&role=${encodeURIComponent(role)}&matchup_type=strong_against`,
		),
		fetch(
			`/counters?champion=${encodeURIComponent(championName)}&role=${encodeURIComponent(role)}&matchup_type=weak_against`,
		),
	]);

	const strongPayload = await strongResponse.json();
	const weakPayload = await weakResponse.json();

	counterSection.hidden = false;
	counterTitle.textContent = `${championName} ${role} matchups`;

	const strongRows = Array.isArray(strongPayload) ? strongPayload : [];
	const weakRows = Array.isArray(weakPayload) ? weakPayload : [];

	if (!strongRows.length && !weakRows.length) {
		counterSubtitle.textContent = "No counter data available for this role yet.";
		renderCounterList(pickAgainstList, [], "No recommended picks found.");
		renderCounterList(avoidIntoList, [], "No avoid list found.");
		return;
	}

	counterSubtitle.textContent = "Strong and weak matchup lists are shown separately for this role.";
	renderCounterList(pickAgainstList, strongRows, "No recommended picks found.");
	renderCounterList(avoidIntoList, weakRows, "No avoid list found.");
}

async function selectChampion(championName) {
	currentChampion = championName;
	closeSuggestions();
	selectedChampionName.textContent = championName;
	setSelectedAvatar(getChampionImageUrl(championName));
	setSearchAvatar(getChampionImageUrl(championName));
	resultsSection.hidden = false;

	currentRoleStats = await fetchRoleStats(championName);
	if (!currentRoleStats.length) {
		selectedChampionMeta.textContent = "No role data found in your database for this champion.";
		roleList.innerHTML = "";
		detailPanel.innerHTML = '<p class="empty-state">No stats found for this champion.</p>';
		counterSection.hidden = true;
		return;
	}

	selectedChampionMeta.textContent = `${currentRoleStats.length} role entries found.`;
	renderRoleButtons(currentRoleStats);
	setActiveRole(currentRoleStats[0].role);
}

function resetSelection() {
	currentChampion = null;
	currentRoleStats = [];
	activeRole = null;

	championSearch.value = "";
	closeSuggestions();
	resultsSection.hidden = true;
	counterSection.hidden = true;
	setSelectedAvatar();
	setSearchAvatar();
}

function setupSearchEvents() {
	// Remove native [hidden] lock from HTML and rely on CSS class toggling.
	suggestionList.hidden = false;
	closeSuggestions();

	championSearch.addEventListener("input", () => {
		if (_isSelecting) return;

		const query = championSearch.value.trim();
		if (!query) {
			closeSuggestions();
			setSearchAvatar();
			return;
		}

		const exact = championByName.get(normalizeName(query));
		if (exact) {
			setSearchAvatar(exact.image_url);
			closeSuggestions();
			return;
		}

		const normalizedQuery = normalizeName(query);
		const matches = championCatalog
			.filter((champion) => normalizeName(champion.champion_name).includes(normalizedQuery))
			.slice(0, 8);

		const first = matches[0];
		if (first) {
			setSearchAvatar(first.image_url);
		} else {
			setSearchAvatar();
		}
		renderSuggestions(matches);
	});

	championSearch.addEventListener("blur", () => {
		setTimeout(() => {
			closeSuggestions();
		}, 80);
	});

	championSearch.addEventListener("keydown", (event) => {
		if (event.key !== "Enter") {
			return;
		}
		event.preventDefault();

		const raw = championSearch.value.trim();
		if (!raw) {
			return;
		}

		const exact = championByName.get(normalizeName(raw));
		if (exact) {
			championSearch.value = exact.champion_name;
			void selectChampion(exact.champion_name);
			closeSuggestions();
			try { championSearch.blur(); } catch (e) {}
			return;
		}

		const fallback = championCatalog.find((champion) =>
			normalizeName(champion.champion_name).includes(normalizeName(raw)),
		);
		if (fallback) {
			championSearch.value = fallback.champion_name;
			void selectChampion(fallback.champion_name);
			closeSuggestions();
			try { championSearch.blur(); } catch (e) {}
		}
	});

	// Close suggestions when clicking outside the whole search panel
	document.addEventListener("click", (event) => {
		const insideSearchPanel = Boolean(event.target.closest(".search-panel"));
		if (!insideSearchPanel) {
			closeSuggestions();
		}
	});


	// Close suggestions on Escape key
	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape") {
			closeSuggestions();
			championSearch.blur();
		}
	});

	// Also close on touchstart for mobile
	document.addEventListener("touchstart", (event) => {
		const insideSearchPanel = Boolean(event.target.closest(".search-panel"));
		if (!insideSearchPanel) {
			closeSuggestions();
		}
	});

	clearChampion.addEventListener("click", resetSelection);
}

async function bootstrap() {
	try {
		await fetchDataDragonChampions();
		setupSearchEvents();
	} catch (error) {
		detailPanel.innerHTML = '<p class="empty-state">Failed to load champion data. Refresh and try again.</p>';
		console.error(error);
	}
}

void bootstrap();
