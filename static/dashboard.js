// Дополнительные функции для дашборда автоассистента

// Глобальные переменные
let currentSection = 'overview';
let charts = {};
let refreshInterval;
let carSortField = null;
let carSortAsc = true;

// Инициализация дашборда
function initializeDashboard() {
    loadDashboardData();
    loadCities();
    loadPopularCars();
    initializeCharts();
    setupEventListeners();
    startAutoRefresh();
    loadBrands();
    loadOptions();
    // Автоматическая подгрузка моделей при выборе бренда
    const brandFilter = document.getElementById('brandFilter');
    if (brandFilter) {
        brandFilter.addEventListener('change', function() {
            loadModels(this.value);
        });
    }
}

// Загрузка данных дашборда
async function loadDashboardData() {
    try {
        // Загружаем статистику
        const statsResponse = await fetch('/api/statistics');
        const stats = await statsResponse.json();
        updateStatistics(stats);

        // Загружаем последние автомобили
        const carsResponse = await fetch('/api/cars?limit=5');
        const carsData = await carsResponse.json();
        const cars = carsData.cars || [];
        populateRecentCarsTable(cars);

        // Загружаем все автомобили
        const allCarsResponse = await fetch('/api/cars');
        const allCarsData = await allCarsResponse.json();
        const allCars = allCarsData.cars || [];
        carsPagination.cars = allCars;
        carsPagination.total = allCars.length;
        carsPagination.page = 1;
        renderCarsTablePage();

        // Загружаем дилерские центры
        const dealersResponse = await fetch('/api/dealers');
        const dealersData = await dealersResponse.json();
        const dealers = dealersData.dealers || [];
        populateDealersTable(dealers);

        // Загружаем аналитику пользователей
        const usersResponse = await fetch('/api/users/analytics');
        const usersAnalytics = await usersResponse.json();
        updateUsersAnalytics(usersAnalytics);

        await renderQuickScenarios();
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        showNotification('Ошибка загрузки данных', 'error');
    }
}

// Обновление статистики
function updateStatistics(stats) {
    document.getElementById('totalCars').textContent = stats.total_cars || 0;
    document.getElementById('totalDealers').textContent = stats.total_dealers || 0;
    document.getElementById('activeUsers').textContent = stats.total_users || 0;
    document.getElementById('avgPrice').textContent = stats.average_price ? 
        (stats.average_price / 1000000).toFixed(1) + 'M' : '0M';
}

// Обновление аналитики пользователей
function updateUsersAnalytics(analytics) {
    document.getElementById('totalUsers').textContent = analytics.total_users || 0;
    document.getElementById('activeSessions').textContent = analytics.active_sessions || 0;
    document.getElementById('newUsers').textContent = analytics.new_users || 0;
    document.getElementById('avgSessionTime').textContent = analytics.avg_session_time || '0 мин';
}

// Инициализация графиков
function initializeCharts() {
    // График продаж
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    charts.sales = new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
            datasets: [{
                label: 'Продажи',
                data: [12, 19, 3, 5, 2, 3],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // График популярных марок
    const brandsCtx = document.getElementById('brandsChart').getContext('2d');
    charts.brands = new Chart(brandsCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });

    // График трендов поиска
    const trendsCtx = document.getElementById('searchTrendsChart').getContext('2d');
    charts.trends = new Chart(trendsCtx, {
        type: 'bar',
        data: {
            labels: ['BMW X5', 'Mercedes GLE', 'Audi Q7', 'Toyota Camry', 'Honda CR-V'],
            datasets: [{
                label: 'Количество поисков',
                data: [65, 59, 80, 81, 56],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe'
                ],
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // График географии
    const geoCtx = document.getElementById('geoChart').getContext('2d');
    charts.geo = new Chart(geoCtx, {
        type: 'pie',
        data: {
            labels: ['Москва', 'СПб', 'Новосибирск', 'Екатеринбург', 'Другие'],
            datasets: [{
                data: [40, 25, 15, 12, 8],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });

    loadGeoChartData();
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработчик формы настроек
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings();
        });
    }

    // Обработчики для мобильного меню
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMobileMenu);
    }

    // Обработчики для фильтров
    setupFilterEventListeners();
}

// Настройка обработчиков фильтров
function setupFilterEventListeners() {
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('input', debounce(applyFilters, 300));
    });
}

// Применение фильтров
function applyFilters() {
    const searchTerm = document.getElementById('searchFilter')?.value || '';
    const brandFilter = document.getElementById('brandFilter')?.value || '';
    const priceFilter = document.getElementById('priceFilter')?.value || '';

    // Применяем фильтры к таблицам
    filterTable('carsTable', searchTerm, brandFilter, priceFilter);
    filterTable('dealersTable', searchTerm);
}

// Фильтрация таблицы
function filterTable(tableId, searchTerm, brandFilter = '', priceFilter = '') {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const brand = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
        const price = row.querySelector('td:nth-child(5)')?.textContent || '';

        const matchesSearch = !searchTerm || text.includes(searchTerm.toLowerCase());
        const matchesBrand = !brandFilter || brand.includes(brandFilter.toLowerCase());
        const matchesPrice = !priceFilter || price.includes(priceFilter);

        if (matchesSearch && matchesBrand && matchesPrice) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Переключение секций
function showSection(sectionId) {
    // Скрываем все секции
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Показываем нужную секцию
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Обновляем активную ссылку в навигации
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeNavItem = document.querySelector(`[onclick="showSection('${sectionId}')"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    currentSection = sectionId;

    // Загружаем данные для секции, если нужно
    loadSectionData(sectionId);
}

// Загрузка данных для конкретной секции
function loadSectionData(sectionId) {
    switch (sectionId) {
        case 'cars':
            loadCarsData();
            break;
        case 'dealers':
            loadDealersData();
            break;
        case 'users':
            loadUsersData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
    }
}

// --- Пагинация для таблицы автомобилей ---
let carsPagination = {
    page: 1,
    perPage: 25,
    cars: [],
    total: 0
};

function renderCarsTablePage() {
    const start = (carsPagination.page - 1) * carsPagination.perPage;
    const end = start + carsPagination.perPage;
    const cars = carsPagination.cars.slice(start, end);
    populateCarsTable(cars);
    renderCarsPaginationControls();
}

function renderCarsPaginationControls() {
    const pag = document.getElementById('carsPagination');
    pag.innerHTML = '';
    const totalPages = Math.ceil(carsPagination.total / carsPagination.perPage);
    const prevBtn = document.createElement('button');
    prevBtn.className = 'btn btn-sm btn-light';
    prevBtn.textContent = 'Назад';
    prevBtn.disabled = carsPagination.page === 1;
    prevBtn.onclick = () => changeCarsPage(-1);
    pag.appendChild(prevBtn);
    for (let i = 1; i <= totalPages; ++i) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm' + (i === carsPagination.page ? ' btn-primary' : ' btn-light');
        btn.textContent = i;
        btn.onclick = () => { carsPagination.page = i; renderCarsTablePage(); };
        pag.appendChild(btn);
    }
    const nextBtn = document.createElement('button');
    nextBtn.className = 'btn btn-sm btn-light';
    nextBtn.textContent = 'Вперёд';
    nextBtn.disabled = carsPagination.page === totalPages;
    nextBtn.onclick = () => changeCarsPage(1);
    pag.appendChild(nextBtn);
}

function changeCarsPage(delta) {
    const totalPages = Math.ceil(carsPagination.total / carsPagination.perPage);
    carsPagination.page = Math.max(1, Math.min(totalPages, carsPagination.page + delta));
    renderCarsTablePage();
}

async function loadCarsData() {
    try {
        const response = await fetch('/api/cars');
        const data = await response.json();
        const cars = data.cars || [];
        carsPagination.cars = cars;
        carsPagination.total = cars.length;
        carsPagination.page = 1;
        renderCarsTablePage();
    } catch (error) {
        console.error('Ошибка загрузки автомобилей:', error);
        showNotification('Ошибка загрузки автомобилей', 'error');
    }
}

// Загрузка данных дилерских центров
async function loadDealersData() {
    try {
        const response = await fetch('/api/dealers');
        const dealers = await response.json();
        populateDealersTable(dealers);
    } catch (error) {
        console.error('Ошибка загрузки дилерских центров:', error);
        showNotification('Ошибка загрузки дилерских центров', 'error');
    }
}

// Загрузка данных пользователей
async function loadUsersData() {
    try {
        const response = await fetch('/api/users/analytics');
        const analytics = await response.json();
        updateUsersAnalytics(analytics);
    } catch (error) {
        console.error('Ошибка загрузки данных пользователей:', error);
        showNotification('Ошибка загрузки данных пользователей', 'error');
    }
}

// Загрузка аналитических данных
async function loadAnalyticsData() {
    try {
        // Загружаем данные для графиков
        const response = await fetch('/api/analytics');
        const analytics = await response.json();
        updateCharts(analytics);
    } catch (error) {
        console.error('Ошибка загрузки аналитики:', error);
        showNotification('Ошибка загрузки аналитики', 'error');
    }
}

// Обновление графиков
function updateCharts(analytics) {
    if (charts.sales && analytics.sales_data) {
        charts.sales.data.datasets[0].data = analytics.sales_data;
        charts.sales.update();
    }

    if (charts.brands && analytics.brands_data) {
        charts.brands.data.datasets[0].data = analytics.brands_data;
        charts.brands.update();
    }

    if (charts.trends && analytics.trends_data) {
        charts.trends.data.datasets[0].data = analytics.trends_data;
        charts.trends.update();
    }
}

// Заполнение таблицы последних автомобилей
function populateRecentCarsTable(cars) {
    const tbody = document.getElementById('recentCarsTable');
    tbody.innerHTML = '';
    if (!cars.length) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align:center;color:#888;">Нет данных</td>';
        tbody.appendChild(row);
        return;
    }
    cars.forEach(car => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${car.brand}</td>
            <td>${car.model}</td>
            <td>${car.year}</td>
            <td>${(car.price / 1000000).toFixed(1)}M ₽</td>
            <td>${car.dealer_center}</td>
            <td>
                <button class="btn btn-primary" onclick="dashboard.editCar(${car.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="dashboard.showDeleteCarModal(${car.id}, '${car.brand} ${car.model}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Заполнение таблицы всех автомобилей
function populateCarsTable(cars) {
    const tbody = document.getElementById('carsTable');
    tbody.innerHTML = '';
    if (!cars.length) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" style="text-align:center;color:#888;">Нет данных</td>';
        tbody.appendChild(row);
        return;
    }
    cars.forEach(car => {
        let extraInfo = '';
        if (car.vin) extraInfo += `<div><b>VIN:</b> ${car.vin}</div>`;
        if (car.color) extraInfo += `<div><b>Цвет:</b> ${car.color}</div>`;
        if (car.body_type) extraInfo += `<div><b>Кузов:</b> ${car.body_type}</div>`;
        if (car.gear_box_type) extraInfo += `<div><b>Коробка:</b> ${car.gear_box_type}</div>`;
        if (car.driving_gear_type) extraInfo += `<div><b>Привод:</b> ${car.driving_gear_type}</div>`;
        if (car.fuel_type) extraInfo += `<div><b>Топливо:</b> ${car.fuel_type}</div>`;
        if (car.power) extraInfo += `<div><b>Мощность:</b> ${car.power}</div>`;
        if (car.mileage) extraInfo += `<div><b>Пробег:</b> ${car.mileage}</div>`;
        if (car.city) extraInfo += `<div><b>Город:</b> ${car.city}</div>`;
        if (car.options && car.options.length) {
            let optionsStr = '';
            if (typeof car.options[0] === 'object') {
                optionsStr = car.options.map(o => o.description || o.code || JSON.stringify(o)).join(', ');
            } else {
                optionsStr = car.options.join(', ');
            }
            extraInfo += `<div><b>Опции:</b> ${optionsStr}</div>`;
        }
        const row = document.createElement('tr');
        row.setAttribute('data-car', JSON.stringify(car));
        row.innerHTML = `
            <td><input type="checkbox" class="car-select-checkbox mass-action-checkbox" value="${car.id}" onchange="updateMassDeleteBtn()"></td>
            <td>${car.brand}</td>
            <td>${car.model}</td>
            <td>${car.year}</td>
            <td>${(car.price/1000000).toFixed(1)}M ₽</td>
            <td>${car.dealer_center}${extraInfo?'<div style=\'font-size:0.9em;color:#555;margin-top:0.3em;\'>'+extraInfo+'</div>':''}</td>
            <td>
                <button class="btn btn-info" title="Подробнее" onclick="showCarDetails(${car.id})"><i class="fas fa-eye"></i></button>
                <button class="btn btn-primary" onclick="dashboard.editCar(${car.id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-danger" onclick="dashboard.showDeleteCarModal(${car.id}, '${car.brand} ${car.model}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Заполнение таблицы дилерских центров
function populateDealersTable(dealers) {
    const tbody = document.getElementById('dealersTable');
    tbody.innerHTML = '';
    if (!dealers.length) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align:center;color:#888;">Нет данных</td>';
        tbody.appendChild(row);
        return;
    }
    dealers.forEach(dealer => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${dealer.id}</td>
            <td>${dealer.name}</td>
            <td>${dealer.address}</td>
            <td>${dealer.phone}</td>
            <td>${dealer.latitude}, ${dealer.longitude}</td>
            <td>
                <button class="btn btn-primary" onclick="dashboard.editDealer(${dealer.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="dashboard.showDeleteDealerModal(${dealer.id}, '${dealer.name}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Функции для работы с автомобилями
function showAddCarModal() {
    // Создаем модальное окно для добавления автомобиля
    const modal = createModal('Добавить автомобиль', createCarForm());
    document.body.appendChild(modal);
}

function editCar(carId) {
    // Загружаем данные автомобиля и показываем форму редактирования
    fetch(`/api/cars/${carId}`)
        .then(response => response.json())
        .then(car => {
            const modal = createModal('Редактировать автомобиль', createCarForm(car));
            document.body.appendChild(modal);
        })
        .catch(error => {
            console.error('Ошибка загрузки автомобиля:', error);
            showNotification('Ошибка загрузки автомобиля', 'error');
        });
}

// Универсальная функция для добавления обработчика закрытия модалки по Esc и клику вне окна
function addModalCloseHandlers(overlay, modalSelector = '.modal-content') {
    // Закрытие по Esc
    function escHandler(e) {
        if (e.key === 'Escape') overlay.remove();
    }
    document.addEventListener('keydown', escHandler);
    // Закрытие по клику вне окна
    overlay.onclick = (e) => {
        if (e.target === overlay) overlay.remove();
    };
    // Удаляем обработчик при удалении модалки
    const observer = new MutationObserver(() => {
        if (!document.body.contains(overlay)) {
            document.removeEventListener('keydown', escHandler);
            observer.disconnect();
        }
    });
    observer.observe(document.body, { childList: true });
}

// Модальное окно подтверждения удаления автомобиля
function showDeleteCarModal(carId, carTitle) {
    const oldModal = document.getElementById('carModalOverlay');
    if (oldModal) oldModal.remove();
    const overlay = document.createElement('div');
    overlay.id = 'carModalOverlay';
    overlay.className = 'modal show';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.3)';
    overlay.style.zIndex = '3000';
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.background = 'white';
    modal.style.borderRadius = '1rem';
    modal.style.minWidth = '320px';
    modal.style.maxWidth = '90vw';
    modal.style.maxHeight = '90vh';
    modal.style.overflow = 'auto';
    modal.style.position = 'relative';
    modal.style.padding = '2rem';
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '1rem';
    closeBtn.style.right = '1rem';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5rem';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => overlay.remove();
    const text = document.createElement('div');
    text.innerHTML = `<b>Удалить автомобиль?</b><br><span style='color:#888;'>${carTitle}</span>`;
    text.style.fontSize = '1.1rem';
    text.style.marginBottom = '1.5rem';
    const btns = document.createElement('div');
    btns.style.display = 'flex';
    btns.style.gap = '1rem';
    const yesBtn = document.createElement('button');
    yesBtn.className = 'btn btn-danger';
    yesBtn.textContent = 'Удалить';
    yesBtn.onclick = async () => {
        await deleteCarConfirmed(carId);
        overlay.remove();
    };
    const noBtn = document.createElement('button');
    noBtn.className = 'btn btn-light';
    noBtn.textContent = 'Отмена';
    noBtn.onclick = () => overlay.remove();
    btns.appendChild(yesBtn);
    btns.appendChild(noBtn);
    modal.appendChild(closeBtn);
    modal.appendChild(text);
    modal.appendChild(btns);
    overlay.appendChild(modal);
    addModalCloseHandlers(overlay);
    document.body.appendChild(overlay);
}

async function deleteCarConfirmed(carId) {
    try {
        const response = await fetch(`/api/cars/${carId}`, { method: 'DELETE' });
            if (response.ok) {
            showNotification('Автомобиль удалён', 'success');
            await loadCarsData();
            await renderQuickScenarios && renderQuickScenarios();
            } else {
                showNotification('Ошибка удаления автомобиля', 'error');
            }
        } catch (error) {
            showNotification('Ошибка удаления автомобиля', 'error');
    }
}

// Функции для работы с дилерскими центрами
function showAddDealerModal() {
    const modal = createModal('Добавить дилерский центр', createDealerForm());
    document.body.appendChild(modal);
}

function editDealer(dealerId) {
    fetch(`/api/dealers/${dealerId}`)
        .then(response => response.json())
        .then(dealer => {
            const modal = createModal('Редактировать дилерский центр', createDealerForm(dealer));
            document.body.appendChild(modal);
        })
        .catch(error => {
            console.error('Ошибка загрузки дилерского центра:', error);
            showNotification('Ошибка загрузки дилерского центра', 'error');
        });
}

// Модальное окно подтверждения удаления дилерского центра
function showDeleteDealerModal(dealerId, dealerTitle) {
    const oldModal = document.getElementById('dealerModalOverlay');
    if (oldModal) oldModal.remove();
    const overlay = document.createElement('div');
    overlay.id = 'dealerModalOverlay';
    overlay.className = 'modal show';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.3)';
    overlay.style.zIndex = '3000';
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.background = 'white';
    modal.style.borderRadius = '1rem';
    modal.style.minWidth = '320px';
    modal.style.maxWidth = '90vw';
    modal.style.maxHeight = '90vh';
    modal.style.overflow = 'auto';
    modal.style.position = 'relative';
    modal.style.padding = '2rem';
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '1rem';
    closeBtn.style.right = '1rem';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5rem';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => overlay.remove();
    const text = document.createElement('div');
    text.innerHTML = `<b>Удалить дилерский центр?</b><br><span style='color:#888;'>${dealerTitle}</span>`;
    text.style.fontSize = '1.1rem';
    text.style.marginBottom = '1.5rem';
    const btns = document.createElement('div');
    btns.style.display = 'flex';
    btns.style.gap = '1rem';
    const yesBtn = document.createElement('button');
    yesBtn.className = 'btn btn-danger';
    yesBtn.textContent = 'Удалить';
    yesBtn.onclick = async () => {
        await deleteDealerConfirmed(dealerId);
        overlay.remove();
    };
    const noBtn = document.createElement('button');
    noBtn.className = 'btn btn-light';
    noBtn.textContent = 'Отмена';
    noBtn.onclick = () => overlay.remove();
    btns.appendChild(yesBtn);
    btns.appendChild(noBtn);
    modal.appendChild(closeBtn);
    modal.appendChild(text);
    modal.appendChild(btns);
    overlay.appendChild(modal);
    addModalCloseHandlers(overlay);
    document.body.appendChild(overlay);
}

async function deleteDealerConfirmed(dealerId) {
    try {
        const response = await fetch(`/api/dealers/${dealerId}`, { method: 'DELETE' });
            if (response.ok) {
            showNotification('Дилерский центр удалён', 'success');
            await loadDealersData();
            } else {
                showNotification('Ошибка удаления дилерского центра', 'error');
            }
        } catch (error) {
            showNotification('Ошибка удаления дилерского центра', 'error');
    }
}

// Создание модального окна
function createModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${title}</h2>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    
    // Закрытие по клику вне модального окна
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    return modal;
}

// Создание формы автомобиля
function createCarForm(car = null) {
    // Динамически подгружаем дилеров
    setTimeout(async () => {
        const select = document.querySelector('#carForm select[name="dealer_center"]');
        if (select) {
            const resp = await fetch('/api/dealers');
            const data = await resp.json();
            (data.dealers || []).forEach(dealer => {
                const opt = document.createElement('option');
                opt.value = dealer.name;
                opt.textContent = dealer.name;
                if (car && car.dealer_center === dealer.name) opt.selected = true;
                select.appendChild(opt);
            });
        }
    }, 0);
    // Формируем форму с расширенными полями
    return `
        <form id="carForm" onsubmit="saveCar(event)">
            <div class="form-group">
                <label class="form-label">Марка</label>
                <input type="text" class="form-input" name="brand" value="${car?.brand || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Модель</label>
                <input type="text" class="form-input" name="model" value="${car?.model || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Год выпуска</label>
                <input type="number" class="form-input" name="year" value="${car?.year || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Цена (руб)</label>
                <input type="number" class="form-input" name="price" value="${car?.price || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">VIN</label>
                <input type="text" class="form-input" name="vin" value="${car?.vin || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Цвет</label>
                <input type="text" class="form-input" name="color" value="${car?.color || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Кузов</label>
                <input type="text" class="form-input" name="body_type" value="${car?.body_type || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Коробка</label>
                <input type="text" class="form-input" name="gear_box_type" value="${car?.gear_box_type || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Привод</label>
                <input type="text" class="form-input" name="driving_gear_type" value="${car?.driving_gear_type || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Топливо</label>
                <input type="text" class="form-input" name="fuel_type" value="${car?.fuel_type || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Мощность (л.с.)</label>
                <input type="number" class="form-input" name="power" value="${car?.power || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Пробег (км)</label>
                <input type="number" class="form-input" name="mileage" value="${car?.mileage || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Город</label>
                <input type="text" class="form-input" name="city" value="${car?.city || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Опции (через запятую)</label>
                <input type="text" class="form-input" name="options" value="${car?.options ? (Array.isArray(car.options) ? car.options.join(', ') : car.options) : ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Дилерский центр</label>
                <select class="form-input" name="dealer_center" required>
                    <option value="">Выберите дилерский центр</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> ${car ? 'Обновить' : 'Добавить'}
            </button>
        </form>
    `;
}

// Создание формы дилерского центра
function createDealerForm(dealer = null) {
    // Динамически подгружаем города (если есть API)
    setTimeout(async () => {
        const select = document.querySelector('#dealerForm select[name="city"]');
        if (select) {
            try {
                const resp = await fetch('/api/cities');
                if (resp.ok) {
                    const data = await resp.json();
                    (data.cities || []).forEach(city => {
                        const opt = document.createElement('option');
                        opt.value = city;
                        opt.textContent = city;
                        if (dealer && dealer.city === city) opt.selected = true;
                        select.appendChild(opt);
                    });
                }
            } catch {}
        }
    }, 0);
    return `
        <form id="dealerForm" onsubmit="saveDealer(event)">
            <div class="form-group">
                <label class="form-label">Название</label>
                <input type="text" class="form-input" name="name" value="${dealer?.name || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Адрес</label>
                <input type="text" class="form-input" name="address" value="${dealer?.address || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Телефон</label>
                <input type="tel" class="form-input" name="phone" value="${dealer?.phone || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Email</label>
                <input type="email" class="form-input" name="email" value="${dealer?.email || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Сайт</label>
                <input type="url" class="form-input" name="website" value="${dealer?.website || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Город</label>
                <select class="form-input" name="city">
                    <option value="">Выберите город</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Широта</label>
                <input type="number" step="any" class="form-input" name="latitude" value="${dealer?.latitude || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Долгота</label>
                <input type="number" step="any" class="form-input" name="longitude" value="${dealer?.longitude || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Описание</label>
                <textarea class="form-input" name="description">${dealer?.description || ''}</textarea>
            </div>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> ${dealer ? 'Обновить' : 'Добавить'}
            </button>
        </form>
    `;
}

// Сохранение автомобиля
async function saveCar(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    let carData = Object.fromEntries(formData.entries());
    // Преобразуем опции в массив
    if (carData.options) {
        carData.options = carData.options.split(',').map(o => o.trim()).filter(Boolean);
    }
    try {
        const response = await fetch('/api/cars/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(carData)
        });
        if (response.ok) {
            showNotification('Автомобиль сохранен', 'success');
            form.closest('.modal').remove();
            await loadCarsData();
        } else {
            showNotification('Ошибка сохранения автомобиля', 'error');
        }
    } catch (error) {
        console.error('Ошибка сохранения автомобиля:', error);
        showNotification('Ошибка сохранения автомобиля', 'error');
    }
}

// Сохранение дилерского центра
async function saveDealer(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const dealerData = Object.fromEntries(formData.entries());
    try {
        const response = await fetch('/api/dealers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dealerData)
        });
        if (response.ok) {
            showNotification('Дилерский центр сохранен', 'success');
            form.closest('.modal').remove();
            await loadDealersData();
            await renderQuickScenarios && renderQuickScenarios();
        } else {
            showNotification('Ошибка сохранения дилерского центра', 'error');
        }
    } catch (error) {
        console.error('Ошибка сохранения дилерского центра:', error);
        showNotification('Ошибка сохранения дилерского центра', 'error');
    }
}

// Сохранение настроек
function saveSettings() {
    const settings = {
        systemName: document.getElementById('systemName').value,
        systemDescription: document.getElementById('systemDescription').value,
        apiVersion: document.getElementById('apiVersion').value
    };

    // Отправляем настройки на сервер
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        if (response.ok) {
            showNotification('Настройки сохранены', 'success');
        } else {
            showNotification('Ошибка сохранения настроек', 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка сохранения настроек:', error);
        showNotification('Ошибка сохранения настроек', 'error');
    });
}

// Показать уведомление
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Переключение мобильного меню
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Автоматическое обновление данных
function startAutoRefresh() {
    setInterval(loadDashboardData, 30000); // каждые 30 секунд
}

// Остановка автоматического обновления
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Функция debounce для оптимизации фильтров
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Загрузка городов для фильтра
async function loadCities() {
    try {
        const resp = await fetch('/api/cities');
        const data = await resp.json();
        const cities = data.cities || data || [];
        // Для фильтра в разделе автомобилей
        const filterCity = document.getElementById('filterCity');
        if (filterCity) {
            filterCity.innerHTML = '<option value="">Все города</option>' + cities.map(city => `<option value="${city}">${city}</option>`).join('');
        }
        // Для фильтра в разделе "Обзор" (если есть)
        const cityFilter = document.getElementById('cityFilter');
        if (cityFilter) {
            cityFilter.innerHTML = '<option value="">Все города</option>' + cities.map(city => `<option value="${city}">${city}</option>`).join('');
        }
    } catch {
        // fallback
    }
}

// Загрузка популярных авто
async function loadPopularCars() {
    try {
        const resp = await fetch('/api/recommendations/popular?limit=5');
        const data = await resp.json();
        const cars = data.cars || [];
        const container = document.getElementById('popularCars');
        if (container) {
            if (!cars.length) {
                container.innerHTML = '<div style="color:#888;">Нет популярных авто</div>';
                return;
            }
            container.innerHTML = cars.map(car => `
                <div class="popular-car-card">
                    <div><b>${car.brand} ${car.model}</b> (${car.year})</div>
                    <div>Город: ${car.city || '-'}</div>
                    <div>Цена: ${(car.price/1000000).toFixed(1)}M ₽</div>
                    <div>Просмотров: ${car.view_count}</div>
                    <button class="btn btn-sm btn-info" onclick="dashboard.showCarDetails(${car.id})">Подробнее</button>
                </div>
            `).join('');
        }
    } catch {}
}

// Просмотр подробной информации по машине
async function showCarDetails(carId) {
    try {
        const resp = await fetch(`/api/cars/${carId}`);
        const data = await resp.json();
        if (data.success && data.car) {
            const car = data.car;
            let html = `<h3>${car.mark} ${car.model} (${car.manufacture_year})</h3>`;
            html += `<div>Город: ${car.city || '-'}</div>`;
            html += `<div>Цена: ${(car.price/1000000).toFixed(1)}M ₽</div>`;
            html += `<div>Дилер: ${car.dealer_center || '-'}</div>`;
            html += `<div>Кузов: ${car.body_type || '-'}</div>`;
            html += `<div>Топливо: ${car.fuel_type || '-'}</div>`;
            html += `<div>Коробка: ${car.gear_box_type || '-'}</div>`;
            html += `<div>Привод: ${car.driving_gear_type || '-'}</div>`;
            html += `<div>VIN: ${car.vin || '-'}</div>`;
            html += `<div>Цвет: ${car.color || '-'}</div>`;
            html += `<div>Мощность: ${car.power || '-'} л.с.</div>`;
            // --- Опции ---
            if (car.options && car.options.length) {
                html += `<div><b>Опции:</b><ul style='margin:0.5em 0 0 1.2em;'>` + car.options.map(o => `<li>${o.description || o.code}</li>`).join('') + `</ul></div>`;
            } else {
                html += `<div><b>Опции:</b> -</div>`;
            }
            openModal('Информация об автомобиле', html);
        } else {
            showNotification('Автомобиль не найден', 'error');
        }
    } catch {
        showNotification('Ошибка загрузки автомобиля', 'error');
    }
}

// Модальное окно для добавления сценария
function showAddScenarioModal() {
    // Удаляем старое модальное окно, если оно есть
    const oldModal = document.getElementById('scenarioModalOverlay');
    if (oldModal) oldModal.remove();
    // Создаём overlay
    const overlay = document.createElement('div');
    overlay.id = 'scenarioModalOverlay';
    overlay.className = 'modal show';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.3)';
    overlay.style.zIndex = '3000';
    // Модальное окно
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.background = 'white';
    modal.style.borderRadius = '1rem';
    modal.style.minWidth = '320px';
    modal.style.maxWidth = '90vw';
    modal.style.maxHeight = '90vh';
    modal.style.overflow = 'auto';
    modal.style.position = 'relative';
    modal.style.padding = '2rem';
    // Кнопка закрытия
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '1rem';
    closeBtn.style.right = '1rem';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5rem';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => overlay.remove();
    // Заголовок
    const title = document.createElement('div');
    title.textContent = 'Добавить быстрый сценарий';
    title.style.fontSize = '1.2rem';
    title.style.fontWeight = '600';
    title.style.marginBottom = '1rem';
    // Форма
    const form = document.createElement('form');
    form.id = 'scenarioForm';
    form.onsubmit = saveScenario;
    form.innerHTML = `
        <div class="form-group">
            <label class="form-label" for="scenarioTitle">Название</label>
            <input type="text" class="form-input" id="scenarioTitle" name="title" required>
        </div>
        <div class="form-group">
            <label class="form-label" for="scenarioIcon">Иконка (emoji или FontAwesome)</label>
            <input type="text" class="form-input" id="scenarioIcon" name="icon">
        </div>
        <div class="form-group">
            <label class="form-label" for="scenarioQuery">Запрос/действие</label>
            <input type="text" class="form-input" id="scenarioQuery" name="query" required>
        </div>
        <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Добавить</button>
    `;
    // Сборка
    modal.appendChild(closeBtn);
    modal.appendChild(title);
    modal.appendChild(form);
    overlay.appendChild(modal);
    addModalCloseHandlers(overlay);
    document.body.appendChild(overlay);
}

// Сохранение быстрого сценария
async function saveScenario(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const scenarioData = Object.fromEntries(formData.entries());
    try {
        const response = await fetch('/api/quick-scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scenarioData)
        });
        if (response.ok) {
            showNotification('Сценарий добавлен', 'success');
            form.closest('.modal').remove();
            await renderQuickScenarios();
        } else {
            showNotification('Ошибка добавления сценария', 'error');
        }
    } catch (error) {
        showNotification('Ошибка добавления сценария', 'error');
    }
}

// Рендеринг быстрых сценариев
async function renderQuickScenarios() {
    try {
        const resp = await fetch('/api/quick-scenarios');
        const data = await resp.json();
        const scenarios = data.scenarios || [];
        const container = document.getElementById('quickScenarios');
        if (!container) return;
        if (!scenarios.length) {
            container.innerHTML = '<div style="color:#888;">Нет быстрых сценариев</div>';
            return;
        }
        container.innerHTML = scenarios.map((s, idx) => `
            <div style="display:flex;align-items:center;gap:0.5rem;background:#fff;border:1px solid #e5e7eb;border-radius:0.5rem;padding:0.5rem 1rem;">
                <button class="btn btn-light" style="background:#fff;font-weight:500;font-size:1rem;display:flex;align-items:center;gap:0.5rem;border:none;box-shadow:none;" onclick="sendQuickMessage('${s.query.replace(/'/g, '\'')}')">
                    <span>${s.icon || ''}</span> ${s.title}
                </button>
                <button class="btn btn-sm" title="Редактировать" style="color:#667eea;background:none;border:none;font-size:1.1rem;" onclick='dashboard.showEditScenarioModal(${JSON.stringify(s)})'>
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm" title="Удалить" style="color:#667eea;background:none;border:none;font-size:1.1rem;" onclick='dashboard.showDeleteScenarioModal(${JSON.stringify(s)})'><i class='fas fa-trash'></i></button>
            </div>
        `).join('');
    } catch {
        // fallback
    }
}

// Модальное окно для редактирования сценария
function showEditScenarioModal(scenario) {
    // Удаляем старое модальное окно, если оно есть
    const oldModal = document.getElementById('scenarioModalOverlay');
    if (oldModal) oldModal.remove();
    // Создаём overlay
    const overlay = document.createElement('div');
    overlay.id = 'scenarioModalOverlay';
    overlay.className = 'modal show';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.3)';
    overlay.style.zIndex = '3000';
    // Модальное окно
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.background = 'white';
    modal.style.borderRadius = '1rem';
    modal.style.minWidth = '320px';
    modal.style.maxWidth = '90vw';
    modal.style.maxHeight = '90vh';
    modal.style.overflow = 'auto';
    modal.style.position = 'relative';
    modal.style.padding = '2rem';
    // Кнопка закрытия
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '1rem';
    closeBtn.style.right = '1rem';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5rem';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => overlay.remove();
    // Заголовок
    const title = document.createElement('div');
    title.textContent = 'Редактировать быстрый сценарий';
    title.style.fontSize = '1.2rem';
    title.style.fontWeight = '600';
    title.style.marginBottom = '1rem';
    // Форма
    const form = document.createElement('form');
    form.id = 'scenarioEditForm';
    form.onsubmit = function(e) { saveEditScenario(e, scenario.id); };
    form.innerHTML = `
        <div class="form-group">
            <label class="form-label" for="scenarioTitleEdit">Название</label>
            <input type="text" class="form-input" id="scenarioTitleEdit" name="title" value="${scenario.title || ''}" required>
        </div>
        <div class="form-group">
            <label class="form-label" for="scenarioIconEdit">Иконка (emoji или FontAwesome)</label>
            <input type="text" class="form-input" id="scenarioIconEdit" name="icon" value="${scenario.icon || ''}">
        </div>
        <div class="form-group">
            <label class="form-label" for="scenarioQueryEdit">Запрос/действие</label>
            <input type="text" class="form-input" id="scenarioQueryEdit" name="query" value="${scenario.query || ''}" required>
        </div>
        <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Сохранить</button>
    `;
    // Сборка
    modal.appendChild(closeBtn);
    modal.appendChild(title);
    modal.appendChild(form);
    overlay.appendChild(modal);
    addModalCloseHandlers(overlay);
    document.body.appendChild(overlay);
}

// Сохранение изменений сценария
async function saveEditScenario(event, scenarioId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const scenarioData = Object.fromEntries(formData.entries());
    try {
        const response = await fetch(`/api/quick-scenarios/${scenarioId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scenarioData)
        });
        if (response.ok) {
            showNotification('Сценарий обновлён', 'success');
            form.closest('.modal.show').remove();
            await renderQuickScenarios();
        } else {
            showNotification('Ошибка обновления сценария', 'error');
        }
    } catch (error) {
        showNotification('Ошибка обновления сценария', 'error');
    }
}

// Модальное окно подтверждения удаления сценария
function showDeleteScenarioModal(scenario) {
    // Удаляем старое модальное окно, если оно есть
    const oldModal = document.getElementById('scenarioModalOverlay');
    if (oldModal) oldModal.remove();
    // Создаём overlay
    const overlay = document.createElement('div');
    overlay.id = 'scenarioModalOverlay';
    overlay.className = 'modal show';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.3)';
    overlay.style.zIndex = '3000';
    // Модальное окно
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.background = 'white';
    modal.style.borderRadius = '1rem';
    modal.style.minWidth = '320px';
    modal.style.maxWidth = '90vw';
    modal.style.maxHeight = '90vh';
    modal.style.overflow = 'auto';
    modal.style.position = 'relative';
    modal.style.padding = '2rem';
    // Кнопка закрытия
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '1rem';
    closeBtn.style.right = '1rem';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5rem';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => overlay.remove();
    // Текст
    const text = document.createElement('div');
    text.innerHTML = `<b>Удалить сценарий?</b><br><span style='color:#888;'>${scenario.title}</span>`;
    text.style.fontSize = '1.1rem';
    text.style.marginBottom = '1.5rem';
    // Кнопки
    const btns = document.createElement('div');
    btns.style.display = 'flex';
    btns.style.gap = '1rem';
    const yesBtn = document.createElement('button');
    yesBtn.className = 'btn btn-danger';
    yesBtn.textContent = 'Удалить';
    yesBtn.onclick = async () => {
        await deleteScenario(scenario.id);
        overlay.remove();
    };
    const noBtn = document.createElement('button');
    noBtn.className = 'btn btn-light';
    noBtn.textContent = 'Отмена';
    noBtn.onclick = () => overlay.remove();
    btns.appendChild(yesBtn);
    btns.appendChild(noBtn);
    // Сборка
    modal.appendChild(closeBtn);
    modal.appendChild(text);
    modal.appendChild(btns);
    overlay.appendChild(modal);
    addModalCloseHandlers(overlay);
    document.body.appendChild(overlay);
}

// Удаление сценария
async function deleteScenario(scenarioId) {
    try {
        const response = await fetch(`/api/quick-scenarios/${scenarioId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Сценарий удалён', 'success');
            await renderQuickScenarios();
        } else {
            showNotification('Ошибка удаления сценария', 'error');
        }
    } catch (error) {
        showNotification('Ошибка удаления сценария', 'error');
    }
}

// Экспорт функций для использования в HTML
window.dashboard = {
    initialize: initializeDashboard,
    showSection,
    showAddCarModal,
    editCar,
    showDeleteCarModal,
    showAddDealerModal,
    editDealer,
    showDeleteDealerModal,
    saveSettings,
    showNotification,
    toggleMobileMenu,
    showCarDetails,
    showAddScenarioModal,
    saveScenario
};

// --- Фильтрация автомобилей ---
function filterCarsTable() {
    const brand = document.getElementById('filterBrand').value.toLowerCase();
    const color = document.getElementById('filterColor').value.toLowerCase();
    const body = document.getElementById('filterBody').value.toLowerCase();
    const city = document.getElementById('filterCity').value.toLowerCase();
    const option = document.getElementById('filterOption').value.toLowerCase();
    const rows = document.querySelectorAll('#carsTable tr[data-car]');
    rows.forEach(row => {
        const car = JSON.parse(row.dataset.car);
        let show = true;
        if (brand && !(car.brand || '').toLowerCase().includes(brand)) show = false;
        if (color && !(car.color || '').toLowerCase().includes(color)) show = false;
        if (body && !(car.body_type || '').toLowerCase().includes(body)) show = false;
        if (city && !(car.city || '').toLowerCase().includes(city)) show = false;
        if (option && !(car.options || []).join(',').toLowerCase().includes(option)) show = false;
        row.style.display = show ? '' : 'none';
    });
}

// --- Сортировка таблицы автомобилей ---
function sortCarsTable(field) {
    const tbody = document.getElementById('carsTable');
    const rows = Array.from(tbody.querySelectorAll('tr[data-car]'));
    carSortAsc = (carSortField === field) ? !carSortAsc : true;
    carSortField = field;
    rows.sort((a, b) => {
        const carA = JSON.parse(a.dataset.car);
        const carB = JSON.parse(b.dataset.car);
        let valA = carA[field] || '';
        let valB = carB[field] || '';
        if (typeof valA === 'number' && typeof valB === 'number') return carSortAsc ? valA - valB : valB - valA;
        return carSortAsc ? (''+valA).localeCompare(''+valB) : (''+valB).localeCompare(''+valA);
    });
    rows.forEach(row => tbody.appendChild(row));
    updateSortIcons();
}

// --- Раскрытие подробностей ---
function toggleCarDetails(row) {
    const details = row.querySelector('.car-details');
    if (details) {
        details.style.display = details.style.display === 'none' ? '' : 'none';
    }
}

// --- Сброс фильтров ---
function resetCarFilters() {
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterColor').value = '';
    document.getElementById('filterBody').value = '';
    document.getElementById('filterCity').value = '';
    document.getElementById('filterOption').value = '';
    document.getElementById('filterPriceMin').value = '';
    document.getElementById('filterPriceMax').value = '';
    document.getElementById('filterYearMin').value = '';
    document.getElementById('filterYearMax').value = '';
    filterCarsTable();
}

// --- Фильтрация с диапазонами ---
function filterCarsTable() {
    const brand = document.getElementById('filterBrand').value.toLowerCase();
    const color = document.getElementById('filterColor').value.toLowerCase();
    const body = document.getElementById('filterBody').value.toLowerCase();
    const city = document.getElementById('filterCity').value.toLowerCase();
    const option = document.getElementById('filterOption').value.toLowerCase();
    const priceMin = parseFloat(document.getElementById('filterPriceMin').value);
    const priceMax = parseFloat(document.getElementById('filterPriceMax').value);
    const yearMin = parseInt(document.getElementById('filterYearMin').value);
    const yearMax = parseInt(document.getElementById('filterYearMax').value);
    const rows = document.querySelectorAll('#carsTable tr[data-car]');
    rows.forEach(row => {
        const car = JSON.parse(row.dataset.car);
        let show = true;
        if (brand && !(car.brand || '').toLowerCase().includes(brand)) show = false;
        if (color && !(car.color || '').toLowerCase().includes(color)) show = false;
        if (body && !(car.body_type || '').toLowerCase().includes(body)) show = false;
        if (city && !(car.city || '').toLowerCase().includes(city)) show = false;
        if (option && !(car.options || []).join(',').toLowerCase().includes(option)) show = false;
        if (!isNaN(priceMin) && car.price/1000000 < priceMin) show = false;
        if (!isNaN(priceMax) && car.price/1000000 > priceMax) show = false;
        if (!isNaN(yearMin) && car.year < yearMin) show = false;
        if (!isNaN(yearMax) && car.year > yearMax) show = false;
        row.style.display = show ? '' : 'none';
    });
}

// --- Визуальные индикаторы сортировки ---
function updateSortIcons() {
    const ths = document.querySelectorAll('th[data-sort]');
    ths.forEach(th => {
        th.querySelector('i').className = 'fas fa-sort';
    });
    if (carSortField) {
        const th = document.querySelector(`th[data-sort="${carSortField}"]`);
        if (th) th.querySelector('i').className = carSortAsc ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
}

// --- Экспорт в CSV ---
function exportCarsToCSV() {
    const rows = document.querySelectorAll('#carsTable tr[data-car]');
    if (!rows.length) return;
    let csv = 'Бренд,Модель,Год,Цена,Дилер\n';
    rows.forEach(row => {
        const car = JSON.parse(row.dataset.car);
        csv += `${car.brand},${car.model},${car.year},${(car.price/1000000).toFixed(1)}M ₽,${car.dealer_center}\n`;
    });
    const blob = new Blob([csv], {type: 'text/csv'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'cars.csv';
    a.click();
}

// --- Быстрый поиск по всем полям ---
function quickSearchCarsTable() {
    const q = document.getElementById('carQuickSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#carsTable tr[data-car]');
    rows.forEach(row => {
        const car = JSON.parse(row.dataset.car);
        const all = Object.values(car).join(' ').toLowerCase();
        row.style.display = all.includes(q) ? '' : 'none';
    });
}

// --- Массовый выбор и удаление ---
function toggleSelectAllCars(checkbox) {
    document.querySelectorAll('.car-select-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateMassDeleteBtn();
}
function updateMassDeleteBtn() {
    const any = Array.from(document.querySelectorAll('.car-select-checkbox')).some(cb => cb.checked);
    document.getElementById('massDeleteBtn').style.display = any ? '' : 'none';
}
function massDeleteCars() {
    const ids = Array.from(document.querySelectorAll('.car-select-checkbox:checked')).map(cb => cb.value);
    if (!ids.length) return;
    if (!confirm('Удалить выбранные автомобили?')) return;
    showLoader('massDeleteBtn');
    fetch('/api/cars/bulk-delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ids})
    }).then(r => r.json()).then(() => {
        hideLoader('massDeleteBtn');
        loadCarsData();
    });
}

// --- Экспорт в Excel (XLSX) ---
function exportCarsToXLSX() {
    const rows = Array.from(document.querySelectorAll('#carsTable tr[data-car]'));
    if (!rows.length) return;
    const headers = Array.from(document.querySelectorAll('#carsTableWrap th')).slice(1,-1).map(th => th.textContent.trim());
    const data = rows.filter(r=>r.style.display!=='none').map(row => {
        const car = JSON.parse(row.dataset.car);
        return headers.map(h => car[h.toLowerCase()] || '');
    });
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);
    XLSX.utils.book_append_sheet(wb, ws, 'Автомобили');
    XLSX.writeFile(wb, 'cars.xlsx');
}

// --- Loader/индикатор ---
function showLoader(btnId) {
    const btn = document.getElementById(btnId);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="loader"></span>';
    }
}
function hideLoader(btnId) {
    const btn = document.getElementById(btnId);
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.origText || btn.textContent;
    }
}

// --- Динамическая загрузка брендов ---
async function loadBrands() {
    try {
        const resp = await fetch('/api/brands');
        const data = await resp.json();
        const brands = data.brands || [];
        const brandFilter = document.getElementById('brandFilter');
        if (brandFilter) {
            brandFilter.innerHTML = '<option value="">Все марки</option>' + brands.map(b => `<option value="${b}">${b}</option>`).join('');
        }
    } catch {}
}

// --- Динамическая загрузка моделей по бренду ---
async function loadModels(brand) {
    try {
        if (!brand) return;
        const resp = await fetch(`/api/models/${encodeURIComponent(brand)}`);
        const data = await resp.json();
        const models = data.models || [];
        const modelFilter = document.getElementById('modelFilter');
        if (modelFilter) {
            let datalist = document.getElementById('modelsDatalist');
            if (!datalist) {
                datalist = document.createElement('datalist');
                datalist.id = 'modelsDatalist';
                modelFilter.setAttribute('list', 'modelsDatalist');
                document.body.appendChild(datalist);
            }
            datalist.innerHTML = models.map(m => `<option value="${m}">`).join('');
        }
    } catch {}
}

// --- Динамическая загрузка опций ---
async function loadOptions() {
    try {
        const resp = await fetch('/api/options');
        const data = await resp.json();
        const options = data.options || [];
        const optionFilter = document.getElementById('filterOption');
        if (optionFilter && optionFilter.tagName === 'SELECT') {
            optionFilter.innerHTML = '<option value="">Все опции</option>' + options.map(o => `<option value="${o.code}">${o.description || o.code}</option>`).join('');
        } else if (optionFilter) {
            let datalist = document.getElementById('optionsDatalist');
            if (!datalist) {
                datalist = document.createElement('datalist');
                datalist.id = 'optionsDatalist';
                optionFilter.setAttribute('list', 'optionsDatalist');
                document.body.appendChild(datalist);
            }
            datalist.innerHTML = options.map(o => `<option value="${o.description || o.code}">`).join('');
        }
    } catch {}
}

async function loadGeoChartData() {
    try {
        // Новый API для статистики по городам
        const resp = await fetch('/api/cities/with-stats');
        const data = await resp.json();
        let cities = data.cities || [];
        // Обработка пустых значений
        cities = cities.map(c => ({
            name: c.name && c.name.trim() ? c.name : 'Не заполнено',
            count: c.count || 0
        }));
        // --- Оставляем только нужные города ---
        const mainCities = ['Ростов-на-Дону', 'Воронеж', 'Краснодар'];
        const cityCounts = { 'Ростов-на-Дону': 0, 'Воронеж': 0, 'Краснодар': 0, 'Другие': 0 };
        cities.forEach(c => {
            if (mainCities.includes(c.name)) {
                cityCounts[c.name] += c.count;
            } else {
                cityCounts['Другие'] += c.count;
            }
        });
        const labels = mainCities.concat('Другие');
        const values = labels.map(l => cityCounts[l]);
        const colors = ['#667eea','#764ba2','#f093fb','#4facfe'];
        if (charts.geo) {
            charts.geo.data.labels = labels;
            charts.geo.data.datasets[0].data = values;
            charts.geo.data.datasets[0].backgroundColor = labels.map((_,i)=>colors[i%colors.length]);
            charts.geo.update();
        }
    } catch (e) {
        console.error('Ошибка загрузки географии:', e);
    }
}
 
 
 
 
 