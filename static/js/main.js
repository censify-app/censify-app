document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');
    const findBtn = document.getElementById('findBtn');
    const searchProgress = document.getElementById('searchProgress');
    const searchResults = document.getElementById('searchResults');
    const videoSelect = document.getElementById('videoSelect');
    const options = document.getElementById('options');
    const processBtn = document.getElementById('processBtn');
    const progressModal = document.getElementById('progressModal');
    const themeToggle = document.getElementById('themeToggle');
    const beepFrequency = document.getElementById('beepFrequency');
    const decreaseFreq = document.getElementById('decreaseFreq');
    const increaseFreq = document.getElementById('increaseFreq');
    const customWords = document.getElementById('customWords');
    const customWordsTags = document.getElementById('customWordsTags');
    const historyToggle = document.getElementById('historyToggle');
    const historySidebar = document.getElementById('historySidebar');
    const commonOptions = document.getElementById('commonOptions');
    
    // Инициализация компонентв Material
    M.Modal.init(document.querySelectorAll('.modal'), {
        dismissible: false, // Запрещаем закрытие по клику вне окна
        opacity: 0.5, // Прозрачность оверлея
        inDuration: 200, // Скорость появления
        outDuration: 200, // Скорость исчезновения
        preventScrolling: true // Запрещаем прокрутку страницы
    });
    M.updateTextFields();
    M.FormSelect.init(document.querySelectorAll('select'));
    
    let searchTimeout;
    let censorWords = new Set();
    
    // Инициализация слайдера частоты только если элемент существует
    const frequencySlider = document.getElementById('frequencySlider');
    if (frequencySlider) {
        noUiSlider.create(frequencySlider, {
            start: [1000],
            connect: true,
            step: 100,
            range: {
                'min': 500,
                'max': 2000
            },
            format: {
                to: value => Math.round(value),
                from: value => Math.round(value)
            }
        });

        // Синхронизация слайдера с полем ввода
        frequencySlider.noUiSlider.on('update', function (values, handle) {
            if (beepFrequency) beepFrequency.value = values[handle];
        });
    }

    // Обработчики частоты только если элементы существуют
    if (beepFrequency) {
        beepFrequency.addEventListener('change', function() {
            let value = parseInt(this.value);
            if (value < 500) value = 500;
            if (value > 2000) value = 2000;
            if (frequencySlider) frequencySlider.noUiSlider.set(value);
        });
    }

    if (decreaseFreq) {
        decreaseFreq.addEventListener('click', function() {
            let value = parseInt(beepFrequency.value) - 100;
            if (value >= 500) {
                beepFrequency.value = value;
                if (frequencySlider) frequencySlider.noUiSlider.set(value);
            }
        });
    }

    if (increaseFreq) {
        increaseFreq.addEventListener('click', function() {
            let value = parseInt(beepFrequency.value) + 100;
            if (value <= 2000) {
                beepFrequency.value = value;
                if (frequencySlider) frequencySlider.noUiSlider.set(value);
            }
        });
    }
    
    // Обработчики поиска
    findBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') performSearch();
    });
    
    // Показ опций при выборе видео
    if (videoSelect) {
        videoSelect.addEventListener('change', function() {
            if (this.value) {
                showOptions();
            }
        });
    }
    
    // Обработчики ввода слов
    customWords.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const word = this.value.trim();
            if (word && !censorWords.has(word)) {
                addWordTag(word);
                this.value = '';
                M.updateTextFields();
            }
        }
    });
    
    // Основные функции поиска и обработки
    function performSearch() {
        const query = searchInput.value.trim();
        if (query.length < 3 && !query.includes('youtube.com')) {
            M.toast({html: 'Введите не менее 3 символов'});
            return;
        }
        
        searchProgress.style.display = 'block';
        searchResults.style.display = 'none';
        
        if (query.includes('youtube.com')) {
            showVideoOption(query);
            searchProgress.style.display = 'none';
        } else {
            searchVideos(query);
        }
    }

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 3 && !query.includes('youtube.com')) return;
        
        searchTimeout = setTimeout(() => {
            if (query.includes('youtube.com')) {
                showVideoOption(query);
            } else {
                searchVideos(query);
            }
        }, 500);
    });
    
    // Обновляем обработчик отправки формы
    processBtn.addEventListener('click', function() {
        const modal = M.Modal.getInstance(progressModal);
        modal.open();
        
        let requestData;
        let headers = {};
        
        if (currentFile) {
            // Для файлов используем FormData
            requestData = new FormData();
            requestData.append('file', currentFile);
            requestData.append('custom_words', JSON.stringify(Array.from(censorWords)));
            requestData.append('use_beep', document.getElementById('useBeep').checked);
            requestData.append('beep_frequency', beepFrequency.value);
        } else {
            // Для YouTube используем JSON
            headers = {
                'Content-Type': 'application/json'
            };
            requestData = JSON.stringify({
                video_url: videoSelect.value,
                custom_words: Array.from(censorWords),
                use_beep: document.getElementById('useBeep').checked,
                beep_frequency: parseInt(beepFrequency.value)
            });
        }
        
        const endpoint = currentFile ? '/process_file' : '/process';
        
        fetch(endpoint, {
            method: 'POST',
            headers: headers,
            body: requestData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const historyItem = addToHistory(
                    currentFile ? currentFile.name : videoSelect.options[videoSelect.selectedIndex].text,
                    `${document.getElementById('useBeep').checked ? 'cb' + beepFrequency.value : 'cs'}_pending`,
                    'pending'
                );
                pollTaskStatus(data.task_id, historyItem, modal);
            } else {
                modal.close();
                M.toast({html: `Ошибка: ${data.error}`});
            }
        })
        .catch(error => {
            modal.close();
            M.toast({html: 'Произошла ошибка при обработке'});
            console.error(error);
        });
    });

    function pollTaskStatus(taskId, historyItem, modal) {
        fetch(`/task/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.state === 'DOWNLOADING') {
                        modal.el.querySelector('h4').textContent = 'Скачивание...';
                    } else if (data.state === 'LOADING_WORDS') {
                        modal.el.querySelector('h4').textContent = 'Загрузка слов...';
                    } else if (data.state === 'CENSORING') {
                        modal.el.querySelector('h4').textContent = 'Цензурирование...';
                    } else if (data.state === 'CLEANING') {
                        modal.el.querySelector('h4').textContent = 'Завершение...';
                    }
                    
                    if (data.file) {
                        // Задача завершена
                        modal.close();
                        historyItem.filename = data.file;
                        historyItem.status = 'success';
                        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
                        updateHistoryUI();
                        window.location.href = `/download/${data.file}`;
                    } else {
                        // Продолжаем опрос
                        setTimeout(() => pollTaskStatus(taskId, historyItem, modal), 1000);
                    }
                } else {
                    modal.close();
                    historyItem.status = 'cancelled';
                    updateHistoryUI();
                    M.toast({html: `Ошибка: ${data.error}`});
                }
            })
            .catch(error => {
                modal.close();
                historyItem.status = 'cancelled';
                updateHistoryUI();
                M.toast({html: 'Произошла ошибка при проверке статуса'});
            });
    }

    // Вспомогательные функции
    function searchVideos(query) {
        fetch(`/search?query=${encodeURIComponent(query)}`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            searchProgress.style.display = 'none';
            if (data.results) {
                updateVideoSelect(data.results);
            } else {
                M.toast({html: 'Ничего не найдено'});
            }
        })
        .catch(error => {
            searchProgress.style.display = 'none';
            M.toast({html: 'Ошибка при поиске'});
            console.error(error);
        });
    }
    
    function formatDuration(seconds) {
        if (!seconds) return "??:??";
        // Преобразуем в целые числа
        const totalSeconds = Math.floor(Number(seconds));
        const minutes = Math.floor(totalSeconds / 60);
        const remainingSeconds = totalSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    function showVideoOption(url) {
        videoSelect.innerHTML = `<option value="${url}" selected>Видео по URL</option>`;
        searchResults.style.display = 'block';
        setTimeout(() => searchResults.classList.add('visible'), 50);
    }
    
    function updateVideoSelect(results) {
        videoSelect.innerHTML = '<option value="" disabled selected>Выберите видео</option>';
        results.forEach(video => {
            const option = document.createElement('option');
            option.value = video.url;
            
            // Создаем контейнер для превью и информации
            const optionContent = document.createElement('div');
            optionContent.style.display = 'flex';
            optionContent.style.alignItems = 'center';
            optionContent.style.gap = '10px';
            
            // Добавляем превью только если оно есть
            if (video.thumbnail) {
                const img = document.createElement('img');
                img.src = video.thumbnail;
                img.alt = 'preview';
                img.style.width = '120px';
                img.style.height = '68px';
                img.style.objectFit = 'cover';
                optionContent.appendChild(img);
            }
            
            // Добавляем текстовую информацию
            const textContent = document.createElement('div');
            textContent.style.flex = '1';
            
            const titleSpan = document.createElement('div');
            titleSpan.textContent = video.title;
            titleSpan.style.fontWeight = 'bold';
            textContent.appendChild(titleSpan);
            
            const infoSpan = document.createElement('div');
            infoSpan.style.fontSize = '0.9em';
            infoSpan.style.color = '#666';
            infoSpan.textContent = `${video.duration} • ${video.channel}`;
            textContent.appendChild(infoSpan);
            
            optionContent.appendChild(textContent);
            option.appendChild(optionContent);
            videoSelect.appendChild(option);
        });
        
        M.FormSelect.init(videoSelect);
        searchResults.style.display = 'block';
        setTimeout(() => searchResults.classList.add('visible'), 50);
    }
    
    function addWordTag(word) {
        const emptyState = document.querySelector('.words-empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        censorWords.add(word);
        const tag = document.createElement('div');
        tag.className = 'censorship-tag';
        tag.innerHTML = `
            ${word}
            <i class="material-icons close">close</i>
        `;
        
        tag.querySelector('.close').addEventListener('click', () => {
            censorWords.delete(word);
            tag.remove();
            
            if (censorWords.size === 0) {
                customWordsTags.innerHTML = `
                    <div class="words-empty-state">
                        <i class="material-icons">info</i>
                        Вы еще не добавили ни одного слова в фильтр
                    </div>
                `;
            }
        });
        
        customWordsTags.appendChild(tag);
    }
    
    updateHistoryUI();

    // Mode switching
    const modeTabs = document.querySelectorAll('.mode-tab:not(.disabled)');
    const modeContents = document.querySelectorAll('.mode-content');
    
    modeTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const mode = tab.dataset.mode;
            
            // Update tabs
            modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Hide all contents with animation
            modeContents.forEach(content => {
                content.classList.add('hiding');
            });
            
            // Show selected content after animation
            setTimeout(() => {
                modeContents.forEach(content => {
                    content.style.display = 'none';
                    content.classList.remove('hiding');
                });
                document.getElementById(`${mode}Mode`).style.display = 'block';
            }, 200);
            
            // Reset options
            commonOptions.style.display = 'none';
        });
    });

    // Initialize tooltips
    M.Tooltip.init(document.querySelectorAll('.tooltipped'));

    // File Upload Handling
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const fileDetails = document.getElementById('fileDetails');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    let currentFile = null;

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    selectFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    removeFile.addEventListener('click', resetFileUpload);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (file && file.type.startsWith('audio/')) {
            currentFile = file;
            dropZone.style.display = 'none';
            fileDetails.style.display = 'flex';
            fileName.textContent = file.name;
            showOptions();
        } else {
            M.toast({html: 'Пожалуйста, выберите аудио файл'});
        }
    }

    function resetFileUpload() {
        currentFile = null;
        fileInput.value = '';
        dropZone.style.display = 'block';
        fileDetails.style.display = 'none';
        commonOptions.style.display = 'none';
    }

    function showOptions() {
        commonOptions.style.display = 'block';
        commonOptions.style.opacity = '0';
        requestAnimationFrame(() => {
            commonOptions.style.opacity = '1';
        });
    }
});

// Константы и функци истории
const HISTORY_KEY = 'censify_history';
let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');

function addToHistory(title, filename, status = 'success') {
    const now = new Date().toISOString();
    const prefix = filename.startsWith('cb') ? 'Гудок' : 'Тишина';
    const freq = filename.startsWith('cb') ? filename.match(/cb(\d+)_/)[1] + ' Гц' : '';
    
    const historyItem = {
        title,
        filename,
        date: now,
        type: prefix,
        frequency: freq,
        status: status
    };
    
    history.unshift(historyItem);
    if (history.length > 10) history.pop();
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    updateHistoryUI();
    return historyItem;
}

function updateHistoryUI() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = history.map((item, index) => `
        <li class="collection-item history-item ${item.status === 'pending' ? 'pending' : ''} ${item.status === 'cancelled' ? 'cancelled' : ''}">
            <div class="history-content">
                <span class="title">${item.title}</span>
                <small class="grey-text">
                    ${item.type}${item.frequency ? ` (${item.frequency})` : ''}
                    <br>
                    ${new Date(item.date).toLocaleString()}
                    ${item.status === 'pending' ? '<br>(обработка...)' : ''}
                    ${item.status === 'cancelled' ? '<br>(отменено)' : ''}
                </small>
            </div>
            <div class="history-actions">
                ${item.status === 'success' ? `
                    <a href="/download/${item.filename}" 
                       class="btn-floating btn-small waves-effect waves-light deep-purple">
                        <i class="material-icons">file_download</i>
                    </a>
                ` : ''}
                <button class="btn-floating btn-small waves-effect waves-light red" 
                        onclick="removeFromHistory(${index})">
                    <i class="material-icons">delete</i>
                </button>
            </div>
        </li>
    `).join('');
}

function removeFromHistory(index) {
    history.splice(index, 1);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    updateHistoryUI();
}

// Тема
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
}

themeToggle.addEventListener('click', function(e) {
    e.preventDefault();
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
});

historyToggle.addEventListener('click', () => {
    historySidebar.classList.toggle('visible');
    const isVisible = historySidebar.classList.contains('visible');
    historyToggle.querySelector('i').textContent = isVisible ? 'close' : 'history';
});

// Обновляем обработчик кликов, добавляя проверку на клик по кнопкам внутри истории
document.addEventListener('click', (e) => {
    if (historySidebar.classList.contains('visible') && 
        !historySidebar.contains(e.target) && 
        !historyToggle.contains(e.target) &&
        !e.target.closest('.btn-floating')) { // Игнорируем клики по кнопкам
        historySidebar.classList.remove('visible');
        historyToggle.querySelector('i').textContent = 'history';
    }
});
