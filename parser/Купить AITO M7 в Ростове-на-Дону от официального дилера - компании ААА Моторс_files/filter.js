import {popup} from "./popup.js";

$(document).ready(function () {

    let $posts = $("#posts");
    let $pagination = $("#cat-paginate");
    let $ul = $("ul.pagination");
    let form = $('#f-buy');

    initLoadMoreVariables();

    modelBlock()

    $.ajaxSetup({
        headers: {
            'X-CSRF-TOKEN': $("[name='csrf-token']").attr('content'),
        }
    });


    function initLoadMoreVariables() {
        // $ul.hide();
        $(".more-cars").click(function (e) {
            e.preventDefault();
            let data = {
                page: $(this).data('page'),
                marks_ids: $('#catalog-pagination').data("marks_ids"),
                models_ids: $('#catalog-pagination').data("models_ids"),
            }
            updateCatalog(data, true, false)
        });

        $("#catalog-pagination a:not(.more-cars)").on('click', function (e) {
            e.preventDefault();
            //добавить марки и модели

            let data = {
                page: $(this).data('page'),
                marks_ids: $('#catalog-pagination').data("marks_ids"),
                models_ids: $('#catalog-pagination').data("models_ids"),

            }
            updateCatalog(data)
        });

    }

    form.on('submit', function (e) {
        $("#catalog-mark").removeClass("is-open")
        // compareInputWithSelect()
        e.preventDefault();
        // updateCatalog()
        $('html, body').animate({scrollTop: $('#posts').position().top - 100}, 500);
    });

    function compareInputWithSelect() {

        compilInputForm(
            $('[data-select="car_body"] > .form-select__main > .not-number'),
            $('[data-select="car_body"] > .form-select__drop > .form-select__drop-item'),
            $('[data-select="car_body"] > .form-select__main > input[name="car_body"]'),
            $('[data-select="car_body"]')
        )

        compilInputForm(
            $('[data-select="gearbox"] > .form-select__main > .not-number'),
            $('[data-select="gearbox"] > .form-select__drop > .form-select__drop-item'),
            $('[data-select="gearbox"] > .form-select__main > input[name="gearbox"]'),
            $('[data-select="gearbox"]')
        )


        // var gearType = 0;
        // $('[data-select="gearbox"] > .form-select__drop > .form-select__drop-item').each(function() {
        //     if($('[data-select="gearbox"] > .form-select__main > .not-number').val().toLowerCase() === $(this).text().toLowerCase().trim()){
        //         gearType = $(this)
        //     }
        // })
        // if(gearType === 0){
        //     $('[data-select="gearbox"] > .form-select__main > .not-number').val('')//input
        //     $('[data-select="gearbox"] > .form-select__main > input[name="gear_type"]').val('')//hide input
        //     $('[data-select="gearbox"]').removeClass('is-active')
        //     $('[data-select="gearbox"] > .form-select__drop > .form-select__drop-item').each(function(index, elem) {//drop item
        //         $(elem).show()
        //     })
        // }
        // else {setSelectFormValue(gearType)}

        compilInputForm(
            $('[data-select="engine_type"] > .form-select__main > .not-number'),
            $('[data-select="engine_type"] > .form-select__drop > .form-select__drop-item'),
            $('[data-select="engine_type"] > .form-select__main > input[name="engine_type"]'),
            $('[data-select="engine_type"]')
        )


        compilInputForm(
            $('[data-select="driving_gear_type"] > .form-select__main > .not-number'),
            $('[data-select="driving_gear_type"] > .form-select__drop > .form-select__drop-item'),
            $('[data-select="driving_gear_type"] > .form-select__main > input[name="driving_gear_type"]'),
            $('[data-select="driving_gear_type"]')
        )


        // var inputValueMin = 0;
        // $('.value-min-container').each(function () {
        //     if ($('.input-value-min').val().toLowerCase() === $(this).text().toLowerCase().trim()) {
        //         $('.input-value-min').val($(this).text().trim())
        //         inputValueMin = 1
        //     }
        // })
        // if (inputValueMin != 1) {
        //     $('.input-value-min').val('')
        // }
        // $('.value-min-container .js-form-select-name').each(function () {
        //     $(this).show()
        // })
        //
        //
        // var inputValueMax = 0;
        // $('.value-max-container').each(function () {
        //     if ($('.input-value-max').val().toLowerCase() === $(this).text().toLowerCase().trim()) {
        //         $('.input-value-max').val($(this).text().trim())
        //         inputValueMax = 1
        //     }
        // })
        // if (inputValueMax != 1) {
        //     $('.input-value-max').val('')
        // }
        // $('.value-max-container .js-form-select-name').each(function () {
        //     $(this).show()
        // })


        var markinput = 0;
        $('.js-mark .check__label').each(function () {
            if ($('.js-mark .markinput').val().toLowerCase() === $(this).text().toLowerCase().trim()) {
                $('.js-mark .markinput').val($(this).text().trim())
                markinput = 1
            }
        })
        if (markinput != 1) {
            $('.js-mark .markinput').val('')
        }
        $('#marks .check__item').each(
            function () {
                $(this).show()
            }
        )

        var modelinput = 0;
        $('.js-model .check__label').each(function () {
            if ($('.js-model .markinput').val().toLowerCase() === $(this).text().toLowerCase().trim()) {
                $('.js-model .markinput').val($(this).text().trim())
                modelinput = 1
            }
        })
        if (modelinput != 1) {
            $('.js-model .markinput').val('')
        }


        compilInputForm($('.input-year-min'),
            $('.year-min-container .form-select__drop-item'),
            null,
            $('.input-year-min'))


        compilInputForm($('.input-year-max'),
            $('.year-max-container .form-select__drop-item'),
            null,
            $('.input-year-max').parent().parent())


    }

    function compilInputForm(input, dropInput, hideInput = null, div) {
        var elem = 0;
        dropInput.each(function () {
            if (input.val().toLowerCase() === $(this).text().toLowerCase().trim()) {
                elem = $(this)
            }
        })
        if (elem === 0) {
            input.val('')//input
            if (hideInput) {
                hideInput.val('')
            } //hide input
            div.removeClass('is-active')
            dropInput.each(function (index, elem) {//drop item
                $(elem).show()
            })
        } else {
            setSelectFormValue(elem)
        }

    }

    let timer;
    $('.f-buy__input').on('input', function (event) {
        const input = $(this)[0];
        let cursorPosition = input.selectionStart;

        // Запоминаем исходное значение и очищаем его от пробелов
        const originalValue = $(this).val();
        const numericValue = originalValue.replace(/\s+/g, '');

        // Парсим очищенное значение как число
        let currentPrice = parseInt(numericValue, 10);

        // Проверяем, что результат парсинга - корректное число, иначе выходим
        if (isNaN(currentPrice)) {
            return;
        }

        // Проверка корректности для поля input-price-max
        if ($(this).hasClass('input-price-max')) {
            let min = parseInt($('.input-price-min').attr('placeholder').replace(/\s+/g, ''), 10);

            if (currentPrice > 0 && currentPrice < min) {
                let errorText = 'Конечное значение цены должно быть больше чем начальное';
                let errorElem = $("<p class='error-price'>" + errorText + "</p>");
                errorElem.css("color", "red").addClass('error-red');
                $('.error-validation .error-price').remove();
                $('.error-validation').append(errorElem);
                return;
            } else {
                $('.error-validation .error-price').remove();
            }
        }

        // Обновляем значение только при изменении
        if (originalValue !== numericValue) {
            $(this).val(numericValue);
        }

        // Очищаем таймер перед повторной установкой
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(function () {
            updateTotalCars();
        }, 1000);

        // Восстанавливаем позицию курсора
        input.setSelectionRange(cursorPosition, cursorPosition);
    });

    $('.js-catalog-city').click(function (e){
        e.preventDefault();
        if ($(this).hasClass('is-active')) {
            return;
        }
        $('.js-catalog-city').removeClass('is-active');
        $(this).addClass('is-active');
        resetFilters();
        // updateTotalCars()
    });
    function updateCatalog(data = {}, append = false, isScroll = true) {

        // Proggress bar
        Pace.restart();


        let formData = new FormData(form[0]);
        let $page = $("#catalog-page");
        let category = $page.attr('data-category');
        if (category) {
            formData.append('category', category);
        }
        let view = $('.js-view-catalog.is-active').attr('data-view');
        if (view) {
            formData.append('view', view);
        }
        let perPage = $('.js-perPage.is-active').attr('data-per-page');
        if (perPage) {
            formData.append('perPage', perPage);
        }
        formData.append('sort', $(".js-catalog-sort select").val());
        formData.append('region_id', $(".js-catalog-city.is-active").data('id'));


        let checked_marks = $('.js-mark').find('input:checked');
        let checked_models = $('.js-model').find('input:checked');
        let marks_ids = [];
        let models_ids = [];
        if (checked_marks.length > 0) {
            checked_marks.map((i, item) => {
                marks_ids.push(item.value)
            })
        }
        if (checked_models.length) {
            checked_models.map((i, item) => {
                models_ids.push(item.value)
            })
        }


        formData.append('marks_ids', marks_ids);
        formData.append('models_ids', models_ids);

        var salonId = window.location.href.split('salon_id=')[1]
        if (salonId) {
            formData.append('salon_id', salonId);
        }


        if (data) {
            for (let key in data) {
                formData.set(key, data[key]);
            }
        }

        updateUrl(category,Object.fromEntries(formData.entries()))

        $.ajax({
            method: 'post',
            processData: false,
            contentType: false,
            cache: false,
            enctype: 'multipart/form-data',
            url: "/catalog",
            data: formData,
            success: function (response) {

                if (isScroll) {
                    $('html, body').animate({scrollTop: $('#posts').position().top - 100}, 1000);
                }


                if (append) {
                    $('#posts').append(
                        $(response.html).children()
                    );
                } else {
                    $('#posts').replaceWith(
                        response.html
                    );
                }

                //пагинация отдельно чтобы работала кнопка показать ещё
                $pagination.html(
                    $(response.pagination)
                );

                // $('#catalog-pagination').attr('data-marks_ids',formData.get('marks_ids'))
                // $('#catalog-pagination').attr('data-models_ids',formData.get('models_ids'))


                initLoadMoreVariables();
                popup();
            },
        })
    }

    function clickOnModelUnderFilter() {
        $('a', '.list-section').on('click', function (e) {
            e.preventDefault();
            let id = $(this).attr('id');
            let markId = $(this).attr('data-mark-id');
            $('.js-mark input:checked').removeAttr("checked");
            $('.js-model input:checked').removeAttr("checked");
            resetSelectMark()
            resetSelectModel()

            if ($(this).hasClass('marks')) {
                $('.js-mark').find(`input[value="${id}"]`).prop('checked', true);
                // updateCatalog({'marks_ids': id}, false, true);

            } else {
                $('.js-mark').find(`input[value="${markId}"]`).prop('checked', true);
                $('.js-model').find(`input[value="${id}"]`).prop('checked', true);
                // updateCatalog({'models_ids': id, 'marks_ids': markId}, false, true);
            }
            clickOnMark()
            // setNameSelectModel()
        });

    }

    clickOnModelUnderFilter();

    function updateUrl(category = null, filters = {}) {
        const removeParams = {
            category: "",
            view: "list",
            perPage: "25"
        };
        if (history.pushState) {
            // Базовый URL каталога
            let baseUrl = window.location.protocol + "//" + window.location.host + "/catalog";

            // Добавляем категорию в URL
            if (category) {
                baseUrl = `${baseUrl}/${category}`;
            }

            // Получаем марки и модели как строки и преобразуем их в массивы
            const marks_ids_str = filters.marks_ids || '';
            const models_ids_str = filters.models_ids || '';
            const marks_ids = marks_ids_str.split(',').filter(id => id !== '');
            const models_ids = models_ids_str.split(',').filter(id => id !== '');

            // Функция для поиска slug по ID в DOM
            function getSlugById(id, type) {
                let element = document.querySelector(`[data-${type}-id="${id}"]`);
                return element ? element.getAttribute(`data-slug`) : null;
            }

            // Получаем марки и модели из фильтров
            const { price_from, price_to, ...otherFilters } = filters;

            // Если выбрана одна марка и одна модель, формируем SEO-friendly URL
            if (marks_ids.length == 1 && models_ids.length == 1) {
                const markSlug = getSlugById(marks_ids[0], 'mark');
                const modelSlug = getSlugById(models_ids[0], 'model');

                if (markSlug && modelSlug) {
                    baseUrl = `${baseUrl}/${markSlug}/${modelSlug}`;
                }
            }
            // Если выбрано только одна марка, но нет модели
            else if (marks_ids.length == 1 && models_ids.length == 0) {
                const markSlug = getSlugById(marks_ids[0], 'mark');

                if (markSlug) {
                    baseUrl = `${baseUrl}/${markSlug}`;
                }
            }

            // Формируем query-параметры для нескольких марок или моделей и остальных фильтров
            let queryParams = [];

            if (marks_ids.length > 1) {
                queryParams.push(`marks_ids=${marks_ids}`);
            }

            if (models_ids.length > 1) {
                queryParams.push(`models_ids=${models_ids}`);
            }

            // Добавляем другие фильтры в query-параметры
            for (const [key, value] of Object.entries(otherFilters)) {
                if (key === 'models_ids' || key === 'marks_ids' || key === 'category') {
                    continue; // Пропускаем текущую итерацию
                }

                if(key === 'view' && value === 'list'){
                    continue
                }

                if(key === 'perPage' && value === '25'){
                    continue
                }

                if (value !== null && value !== undefined && value !== '') {
                    queryParams.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
                }
            }

            // Если есть query-параметры, добавляем их к URL
            if (queryParams.length > 0) {
                baseUrl += `?${queryParams.join('&')}`;
            }

            // Обновляем URL без перезагрузки страницы
            history.pushState(null, null, baseUrl.replace(/\s/g, ''));
        } else {
            console.warn('History API не поддерживается');
        }
    }


    $(".js-power").bind("change keyup keydown input click", function () {
        if (this.value.match(/[^0-9]/g)) {
            this.value = this.value.replace(/[^\d\.,]/g, "");
            this.value = this.value.replace(/,/g, ".");

        }

        if (this.value.match(/\./g)) {
            this.value = this.value.substr(0, this.value.lastIndexOf("."));
        }

    });


    $(".js-form-select-name").on("click", function () {
        setSelectFormValue($(this));
    });

    function setSelectFormValue(elem) {
        if (!elem.hasClass('__hide')){
            let name = elem.text().trim() === 'Любой' ? null : elem.text().trim();
            let id = elem.data('id');
            let parent = elem.parents(".js-form-select");
            parent.find(".js-form-select-input").val(name);
            parent.find(".js-form-select-input:hidden").val(id);
            CompareValue(elem.parent().parent().find(".js-form-select-input"));
            parent.addClass('is-full')
            updateTotalCars();
        }

    }
    function renderCapacities(capacities) {
        const startCapacityContainer = $('.value-min-container');
        const endCapacityContainer = $('.value-max-container');


        // Создаем фрагменты для добавления элементов
        let startItems = [];
        let endItems = [];

        // Добавляем общий "Любой" элемент
        const anyItem = (containerClass) =>
            $('<div>', {
                text: 'Любой',
                class: `form-select__drop-item js-form-select-name ${containerClass}`
            });

        // Генерируем элементы для обоих контейнеров
        capacities.forEach(item => {
            const isActiveClass = item.isActive ? '' : '__hide';

            startItems.push(
                $('<div>', {
                    text: item.value,
                    class: `form-select__drop-item js-form-select-name value-min ${isActiveClass}`
                })
            );

            // Добавляем в начало для обратного порядка
            endItems.unshift(
                $('<div>', {
                    text: item.value,
                    class: `form-select__drop-item js-form-select-name value-max ${isActiveClass}`
                })
            );
        });

        startItems.unshift(anyItem('value-min'));
        endItems.unshift(anyItem('value-max'));

        // Очищаем и добавляем все элементы за один раз
        startCapacityContainer.empty().append(startItems);
        endCapacityContainer.empty().append(endItems);

        // Добавляем обработчики событий через делегирование
        $('.value-min-container, .value-max-container').on('click', '.value-min, .value-max', function() {
            setSelectFormValue($(this));
        });

        // Обновляем placeholder на основе значений из capacities
        if (capacities.length > 0) {
            // Фильтруем только активные элементы
            const activeCapacities = capacities.filter(item => item.isActive);

            if (activeCapacities.length > 0) {
                // Находим минимальное и максимальное значение среди активных элементов
                const minCapacity = Math.min(...activeCapacities.map(item => item.value)) ?? 0;
                const maxCapacity = Math.max(...activeCapacities.map(item => item.value)) ?? 0;

                // Обновляем placeholder
                $('.input-value-min').attr('placeholder', `Объем от ${minCapacity} л`);
                $('.input-value-max').attr('placeholder', `До ${maxCapacity} л`);
            } else {
                // Если нет активных элементов, устанавливаем placeholder по умолчанию
                $('.input-value-min').attr('placeholder', 'Объем от 0 л');
                $('.input-value-max').attr('placeholder', 'До 0 л');
            }
        }
    }


    // $(".input-price-min").on("blur", function () {
    //
    //     let priceMin = $(".input-price-min").attr('placeholder').substring(8).replaceAll(' ', '');
    //     let val = $(this).val().replaceAll(' ', '');
    //
    //     if (parseFloat(val) < priceMin) {
    //         $(this).val(trimInteger(priceMin));
    //     }
    //
    // });


    $(".f-buy__input").on("input", function () {
        $(this).val(trimInteger($(this).val()))
    })


    // $(".input-milage-min").on("input blur" , function(){
    //
    //     let milageMin = $(".input-milage-min").attr('placeholder');
    //     milageMin = milageMin.replaceAll(' ', '');
    //     milageMin = parseInt(milageMin.match(/\d+/))
    //     let errorText = 'Минимальное значение пробега не может быть меньше '+milageMin;
    //
    //     if(parseInt($(this).val().replaceAll(' ', '')) < milageMin){
    //        let errorElem = $("<p class='error-milage-min'>"+errorText+"</p>");
    //         $(this).css('color', 'red');
    //
    //         if(!checkPErrorTag(errorText)){
    //             errorElem.css("color", "red");
    //             $('.error-validation').append(errorElem);
    //         }
    //
    //     }else{
    //         if(checkPErrorTag(errorText) ){
    //             $('.error-milage-min').remove();
    //         }
    //
    //         if(!checkPErrorTag('Конечное значение пробега должно быть меньше чем начальное')
    //             && !checkPErrorTag(errorText)
    //         ){
    //             $('.input-milage-min').css('color', '');
    //         }
    //
    //
    //     }
    //
    // });


    function CompareValue(elem) {

        let minElem = null;
        let maxElem = null;
        let errorText = '';
        let errorElem = '';
        let errorClass = '';

        if (elem.hasClass("input-year-max") || elem.hasClass("input-year-min")) {

            minElem = $('.input-year-min');
            maxElem = $('.input-year-max');
            // errorText = 'Конечное значение года должно быть больше чем начальное';
            errorElem = $("<p class='error-year'>" + errorText + "</p>");
            errorClass = '.error-year';

        } else if (elem.hasClass("input-value-min") || elem.hasClass("input-value-max")) {

            minElem = $('.input-value-min');
            maxElem = $('.input-value-max');
            // errorText = 'Конечное значение объёма должно быть больше чем начальное';
            errorElem = $("<p class='error-value'>" + errorText + "</p>");
            errorClass = '.error-value';

        } else if (elem.hasClass("input-milage-min") || elem.hasClass("input-milage-max")) {

            minElem = $('.input-milage-min');
            maxElem = $('.input-milage-max');
            // errorText = 'Конечное значение пробега должно быть больше чем начальное';
            errorElem = $("<p class='error-milage'>" + errorText + "</p>");
            errorClass = '.error-milage';


        } else if (elem.hasClass("input-price-min") || elem.hasClass("input-price-max")) {

            minElem = $('.input-price-min');
            maxElem = $('.input-price-max');
            // errorText = 'Конечное значение цены должно быть больше чем начальное';
            errorElem = $("<p class='error-price'>" + errorText + "</p>");
            errorClass = '.error-price';


        }


        if (maxElem && minElem) {
            if (parseInt(maxElem.val().replaceAll(' ', '')) < parseInt(minElem.val().replaceAll(' ', ''))
                && parseInt(minElem.val().replaceAll(' ', '')) > 0 && parseInt(maxElem.val().replaceAll(' ', '')) > 0) {
                elem.css('color', 'red');
                if (!checkPErrorTag(errorText)) {
                    errorElem.css("color", "red");
                    errorElem.addClass('error-red')
                    $('.error-validation').append(errorElem);
                }

            } else {
                if (checkPErrorTag(errorText)) {
                    $(errorClass).remove();
                }
                minElem.css('color', '');
                maxElem.css('color', '');
            }

            // compareWithMaxOrMin(elem);

        }

    }

    $(".input-price-min, .input-price-max, .input-milage-max, .input-milage-min").on("input blur", function () {

        CompareValue($(this))

    })

    function compareAfterUpdateCategory() {

        CompareValue($('.input-year-max'));
        CompareValue($('.input-year-min'));
        CompareValue($('.input-price-min'));
        CompareValue($('.input-price-max'));
        CompareValue($('.input-milage-min'));
        CompareValue($('.input-milage-max'));
        CompareValue($('.input-value-min'));
        CompareValue($('.input-value-max'));

    }


    function compareWithMaxOrMin(elem) {

        let max = null;
        let min = null;
        let errorText = "";
        let errorElem = null;
        let errorClass = "";

        if (elem.hasClass("input-year-min")) {
            min = elem.attr('placeholder');
            min = parseInt(min.match(/\d+/));
            max = parseInt(elem.val().replaceAll(' ', ''));
            errorText = 'Значение года "ОТ" должно быть больше ' + trimIntegerYear(min);
            errorElem = $("<p class='error-year-min'>" + errorText + "</p>");
            errorClass = '.error-year-min';
        }
            // else if (elem.hasClass("input-year-max")) {
            //     max = elem.attr('placeholder');
            //     max = parseInt(max.match(/\d+/));
            //     min = parseInt(elem.val().replaceAll(' ', ''));
            //     errorText = 'Значение года "ДО" должно быть меньше ' + trimIntegerYear(max);
            //     errorElem = $("<p class='error-year-max'>" + errorText + "</p>");
            //     errorClass = '.error-year-max';
            // }
            // else if (elem.hasClass("input-milage-max")) {
            //     min = parseInt(elem.val().replaceAll(' ', ''));
            //     max = elem.attr('placeholder').replaceAll(' ', '');
            //     max = parseInt(max.match(/\d+/));
            //     errorText = 'Максимальное значение пробега в данной выборке ' + trimInteger(max);
            //     errorElem = $("<p class='error-milage-max'>" + errorText + "</p>");
            //     errorClass = '.error-milage-max';
        // }
        else if (elem.hasClass("input-milage-min")) {
            min = elem.attr('placeholder').replaceAll(' ', '');
            min = parseInt(min.match(/\d+/));
            max = parseInt(elem.val().replaceAll(' ', ''));
            errorText = 'Минимальное значение пробега в данной выборке ' + trimInteger(min);
            errorElem = $("<p class='error-milage-min'>" + errorText + "</p>");
            errorClass = '.error-milage-min';
        } else if (elem.hasClass("input-price-min")) {
            min = elem.attr('placeholder').replaceAll(' ', '');
            min = parseInt(min.match(/(\d+(\.\d+)?)/));
            max = parseInt(elem.val().replaceAll(' ', ''));
            errorText = 'Минимальное значение цены в данной выборке ' + trimInteger(min);
            errorElem = $("<p class='error-price-min'>" + errorText + "</p>");
            errorClass = '.error-price-min';
        }
            // else if (elem.hasClass("input-price-max")) {
            //     max = elem.attr('placeholder').replaceAll(' ', '');
            //     max = parseInt(max.match(/\d+/));
            //     min = parseInt(elem.val().replaceAll(' ', ''));
            //     errorText = 'Максимальное значение цены в данной выборке ' + trimInteger(max);
            //     errorElem = $("<p class='error-price-max'>" + errorText + "</p>");
            //     errorClass = '.error-price-max';
        // }
        else if (elem.hasClass("input-value-min")) {
            min = elem.attr('placeholder').replaceAll(' ', '');
            min = min.replace(/[A-Za-zА-Яа-яЁё]/g, '');
            max = parseFloat(elem.val().replaceAll(' ', ''));
            errorText = `Минимальное значение объёма в данной выборке -  ${min} л`;
            errorElem = $("<p class='error-value-min'>" + errorText + "</p>");
            errorClass = '.error-value-min';
        }
        // else if (elem.hasClass("input-value-max")) {
        //     max = elem.attr('placeholder').replaceAll(' ', '');
        //     max = parseFloat(max.match(/(\d+(\.\d+)?)/));
        //     min = parseFloat(elem.val().replaceAll(' ', ''));
        //     errorText = `Максимальное значение объёма в данной выборке -  ${max} л`;
        //     errorElem = $("<p class='error-value-max'>" + errorText + "</p>");
        //     errorClass = '.error-value-max';
        // }


        checkAndAddOrRemoveError(min, max, errorText, errorElem, errorClass, elem)

        if (elem.hasClass("input-milage-min") && !$('.input-milage-max').val().length) {
            max = $('.input-milage-max').attr('placeholder').replaceAll(' ', '');
            max = parseInt(max.match(/\d+/));
            min = parseInt(elem.val().replaceAll(' ', ''));
            errorText = 'Минимальное значение пробега не может быть больше ' + max;
            errorElem = $("<p class='error-milage-min'>" + errorText + "</p>");
            errorClass = '.error-milage-min';
            checkAndAddOrRemoveError(min, max, errorText, errorElem, errorClass, elem)
        }

        if (elem.hasClass("input-price-min") && !$('.input-price-max').val().length) {
            max = $('.input-price-max').attr('placeholder').replaceAll(' ', '');
            max = parseInt(max.match(/\d+/));
            min = parseInt(elem.val().replaceAll(' ', ''));
            errorText = 'Минимальное значение цены не может быть больше ' + max;
            errorElem = $("<p class='error-price-min'>" + errorText + "</p>");
            errorClass = '.error-price-min';
            checkAndAddOrRemoveError(min, max, errorText, errorElem, errorClass, elem)
        }


    }

    function checkAndAddOrRemoveError(min, max, errorText, errorElem, errorClass, elem) {
        //добавляет или удаляет сообщение об ошибке

        if (max >= 0 && min >= 0 && max < min) {
            if (errorText.indexOf('в данной выборке') > -1
            ) {
                elem.css('color', 'blue');
                errorElem.css('color', 'blue');
            } else {
                elem.css('color', 'red');
                errorElem.css('color', 'red');
                errorElem.addClass('error-red')
            }


            if (!checkPErrorTag(errorText)) {
                $('.error-validation').append(errorElem);

            }
        } else {
            if (checkPErrorTag(errorText)) {
                $(errorClass).remove();
            }

            if (!checkPErrorTag('Конечное значение года должно быть больше чем начальное')
                && !checkPErrorTag(errorText) && elem.hasClass("input-year-max")
            ) {
                $('.input-year-min').css('color', '');
            } else if (!checkPErrorTag('Конечное значение пробега должно быть больше чем начальное')
                && !checkPErrorTag(errorText) && elem.hasClass("input-milage-max")
            ) {
                $('.input-milage-min').css('color', '');
            } else if (!checkPErrorTag('Конечное значение цены должно быть больше чем начальное')
                && !checkPErrorTag(errorText) && elem.hasClass("input-price-min")
            ) {
                $('.input-price-min').css('color', '');
            } else if (!checkPErrorTag('Конечное значение объёма должно быть больше чем начальное')
                && !checkPErrorTag(errorText) && elem.hasClass("input-value-min")
            ) {
                $('.input-value-min').css('color', '');
            }

        }


        if (elem.hasClass("input-milage-max")
            && checkPErrorTag('Минимальное значение пробега в данной выборке')) {
            $('.input-milage-min').css('color', 'blue');
        }
            // else if (elem.hasClass("input-milage-min") && checkPErrorTag('Максимальное значение пробега в данной выборке')) {
            //     $('.input-milage-max').css('color', 'blue');
        // }
        else if (elem.hasClass("input-year-max")
            && checkPErrorTag('Значение года "ОТ" должно быть больше')) {
            $('.input-year-min').css('color', 'red');
        } else if (elem.hasClass("input-year-min") && checkPErrorTag('Значение года "ДО" должно быть меньше')) {
            $('.input-year-max').css('color', 'red');
        } else if (elem.hasClass("input-price-max")
            && checkPErrorTag('Минимальное значение цены в данной выборке')) {
            $('.input-price-min').css('color', 'blue');
        }
            // else if (elem.hasClass("input-price-min") && checkPErrorTag('Максимальное значение цены в данной выборке')) {
            //     $('.input-price-max').css('color', 'blue');
        // }
        else if (elem.hasClass("input-value-max")
            && checkPErrorTag('Минимальное значение объёма не может быть меньше')) {
            $('.input-value-min').css('color', 'red');
        }
        // else if (elem.hasClass("input-value-min") && checkPErrorTag('Максимальное значение объёма не может быть больше')) {
        //     $('.input-value-max').css('color', 'red');
        // }

    }

    function checkPErrorTag(error) {
        let errorText = error.replace(/\d+/g, "").trim();
        errorText = errorText.slice(0, -3)
        let res = false;
        $('.error-validation').children('p').each(function () {

            if ($(this).text().indexOf(errorText) > -1) {
                res = true;
            }
        });

        return res;
    }

    $('.year-min').on("click", function () {
        let year = $(this).text().trim() === 'Любой' ? null : $(this).text().trim();
        insertYearMax(year);
    });


    function insertYearMax(min) {
        let date = $(".input-year-max").attr('placeholder').slice(3);//new Date().getFullYear();
        $('.year-max-container').empty();

        min ??= 1980;
        if (min == 0) {
            min = 1980
        }


        for (let i = min; i <= date; i++) {
            $('.year-max-container').append($('<div >', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name year-max'
            }));
        }

        $('.year-max-container').append($('<div >', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name year-max'
        }));

        $(".year-max").on("click", function () {
            setSelectFormValue($(this));
        });
    }


    $('.year-max').on("click", function () {
        let year = $(this).text().trim() === 'Любой' ? null : $(this).text().trim();
        insertYearMin(year);
    });

    function insertYearMin(max) {
        let date = new Date().getFullYear();
        $('.year-min-container').empty();
        max ??= new Date().getFullYear();
        let minYear = $(".input-year-min").attr('placeholder').slice(7);
        if (!minYear) {
            minYear = $(".input-year-min").attr('placeholder');
        }


        if (minYear == 0) {
            minYear = new Date().getFullYear()
        }

        for (let i = minYear; i <= max; i++) {
            $('.year-min-container').append($('<div >', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name year-min'
            }));
        }

        $('.year-min-container').append($('<div >', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name year-min'
        }));


        $(".year-min").on("click", function () {
            setSelectFormValue($(this));
        });
    }

    $('.value-min').on("click", function () {
        let min = $(this).text().trim() === 'Любой' ? null : $(this).text().trim();
        // insertValueMax(min);
    });

    function insertValueMax(min) {

        $('.value-max-container').empty();
        min ??= 0;

        for (let i = min; i <= 10; i++) {

            $('.value-max-container').append($('<div>', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name value-max'
            }));
        }

        $('.value-max-container').append($('<div>', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name value-max'
        }));

        $(".value-max").on("click", function () {
            setSelectFormValue($(this));
        });
    }

    $('.value-max').on("click", function () {
        let max = $(this).text().trim() === 'Любой' ? null : $(this).text().trim();
        // insertValueMin(max);
    });

    function insertValueMin(max) {

        $('.value-min-container').empty();
        max ??= 10;

        for (let i = 0; i <= max; i++) {

            $('.value-min-container').append($('<div>', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name value-min'
            }));
        }

        $('.value-min-container').append($('<div>', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name value-min'
        }));

        $(".value-min").on("click", function () {
            setSelectFormValue($(this));
        });
    }

    function trimInteger(int) {

        int = String(int);
        int = int.replaceAll(' ', '');
        return (int + '').replace(/(\d)(?=(\d\d\d)+([^\d]|$))/g, '$1 ');

    }

    function trimIntegerYear(intYear) {

        intYear = String(intYear);
        intYear = intYear.replaceAll(' ', '');
        return (intYear + '').replace(/(\d)(?=(\d\d\d)+([^\d]|$))/g, '$1');

    }

    function updateTotalCars(update_marks = true, update_category = null) {
        // не обновляет если есть ошибки красного цвета если синего обновляет
        if ($('.error-red').length < 1) {
            let formData = new FormData(document.getElementById('f-buy'));
            let checked_marks = $('.js-mark').find('input:checked');
            let checked_models = $('.js-model').find('input:checked')

            let category = $("#catalog-page").attr('data-category');
            if (update_category) {
                formData.append('category', update_category.category);
            } else {
                formData.append('category', category);
            }

            //
            let view = $('.js-view-catalog.is-active').attr('data-view');
            if (view) {
                formData.append('view', view);
            }
            let perPage = $('.js-perPage.is-active').attr('data-per-page');
            if (perPage) {
                formData.append('perPage', perPage);
            }
            formData.append('sort', $(".js-catalog-sort select").val());
            formData.append('region_id', $(".js-catalog-city.is-active").data('id'));


            // children('.is-active').
            // .parent().parent().parent().parent().hasClass('is-active');

            let marks_ids = [];
            let models_ids = [];
            if (checked_marks.length > 0) {
                checked_marks.map((i, item) => {
                    marks_ids.push(item.value)
                })
            }
            if (checked_models.length > 0) {
                checked_models.map((i, item) => {
                    models_ids.push(item.value)
                })
            }

            var salonId = window.location.href.split('salon_id=')[1]
            if (salonId) {
                formData.append('salon_id', salonId);
            }


            formData.append('marks_ids', marks_ids);
            formData.append('models_ids', models_ids);
            formData.set('price[max]', formData.get('price[max]').replaceAll(' ', ''))
            formData.set('price[min]', formData.get('price[min]').replaceAll(' ', ''))
            formData.set('mileage[min]', formData.get('mileage[min]').replaceAll(' ', ''))
            formData.set('mileage[max]', formData.get('mileage[max]').replaceAll(' ', ''))


            $.ajax({
                method: 'post',
                processData: false,
                contentType: false,
                cache: false,
                enctype: 'multipart/form-data',
                url: "/catalog",
                data: formData,
                success: function (response) {
                    //при клике на категории обновляет машины сразу
                    //также обновляет сразу машины при выборе в фильтре без нажатия на кнопку Показать 40 авто
                    updateUrl(category,Object.fromEntries(formData.entries()))
                    $('#posts').replaceWith(
                        response.html
                    );

                    renderCapacities(response.filters.capacities ?? []);

                    $('.js-category-title').text(response.title);
                    document.title = response.meta_title;

                    //пагинация отдельно чтобы работала кнопка показать ещё
                    $pagination.html($(response.pagination));
                    initLoadMoreVariables();

                    // updateModels(response)
                    if (update_category) {
                        resetSelectModel()
                        updateCategory(response)
                    } else {
                        updateCategory(response, false);
                    }

                    if (update_marks) {
                        updateMarksCount(response.filtered_marks)
                    }

                    $('#filtered_models').html(response.filtered_models_html);
                    modelBlock()

                    if (checked_marks.length > 0) {
                        updateModelsCount(response.filtered_models)
                    }


                    $('.js-total-cars').text(response.total_cars);

                    if (response.total_cars === 0) {
                        $('#filtered_models').hide()
                        $('.empty-results').remove();
                        $('.error-validation').append("<p class='empty-results'>Ничего не найдено</p>")
                    } else {
                        $('#filtered_models').show()
                        $('.empty-results').remove();
                    }

                    clickOnModelUnderFilter()

                    popup();
                },
            })
        }
    }

    function updateModelsCount(models) {

        $('.js-model .check__item').each(function () {

            let modelId = Number($(this).find('input').val());
            let model = models.find(function (element) {
                return element.id === modelId
            });

            if (model) {
                let count = model.filtered_cars_count
                $(this).find('.check__count').text(count)
                $(this).show()
            } else {
                $(this).find('.check__count').text(0)
                $(this).hide()
            }


        })

    }


    function updateMarksCount(marks) {

        $('.marks-menu .check__item').each(function () {
            let markId = Number($(this).find('input').val());
            let mark = marks.find(function (element) {
                return element.id === markId
            });

            if (mark) {
                let count = mark.filtered_cars_count
                $(this).show()
                $(this).find('.check__count').text(count)
            } else {
                $(this).find('.check__count').text(0)
                $(this).hide()
            }
        })

    }


    $(".js-form-select-input").on("focus", function () {
        $(this).parents(".js-form-select").addClass("is-active");
    });

    $(".js-form-select-input").on("blur", function () {


        let value = $(this).val().length,
            parents = $(this).parents(".js-form-select");

        let elem = $(this).parent().parent();

        let timer = setTimeout(function (elem) {

            elem.removeClass("is-active");

            if (value > 0) {
                $(parents).addClass("is-full");
            }

        }, 150, elem);


    });

    $(".js-model input").on("click", function () {
        setNameSelectModel()
    });


    function setNameSelectModel(update = true) {
        //вот тут не упдейтить если не упдэйт
        var nameString = "";
        var model_count = 0,
            tab_number = 0;

        $(".js-model .js-tab-small-block").each(function (index, elem) {
            var activeItem = 0;
            $(elem).find("input").each(function (index, elem) {
                // if ($(elem).is(':checked') && $(elem).parent().parent().parent().parent().hasClass('is-active')) {
                if ($(elem).is(':checked')) {
                    let name = $(elem).parents(".check__item").find(".check__label").text();
                    model_count = model_count + 1;
                    activeItem = activeItem + 1;
                    if (activeItem > 1) {
                        nameString = nameString + ", " + name;
                    } else {
                        nameString = nameString + "/" + name;
                    }
                }
            });
        });


        if (model_count != 0) {
            if (nameString[0] == "/") {
                nameString = nameString.slice(1);
            }
            if (nameString[0] == " ") {
                nameString = nameString.slice(1);
            }
            nameString = nameString + "(" + model_count + ")";
            $(".js-model").addClass("is-full");
        } else {
            $(".js-model").removeClass("is-full");
        }
        nameString = nameString.length > 0 ? nameString : 'Модель';
        $(".js-model .js-check-select-main span").text(nameString)
        if (update){
            updateTotalCars(false);
        }
    }

    $(".js-filter-up").on('click', function (e) {
        e.preventDefault();
        $('html, body').animate({scrollTop: $(".js-buy-form").position().top - 110}, '300');
    });

    $(window).scroll(function () {
        if ($(".list-section").length > 0 && ($(window).scrollTop() > $(".list-section").position().top)) {
            $(".js-filter-tag").addClass("is-show");
        } else {
            $(".js-filter-tag").removeClass("is-show");
        }
    });


    // Поиск по маркам с клавиатуры
    $(".js-search-list").on("input , keyup, ", function () {

        let parents = $(this).parents(".js-check-select");
        var value = $(this).val().toLowerCase();
        $(parents).find(".check__item").each(function (index, elem) {

            if ($(elem).find(".check__label").text().toLowerCase().indexOf(value) > -1) {
                $(elem).show();
            } else {
                $(elem).hide();
            }

        });
    });

    //Поиск по вводу названия с клвиатуры
    $(".js-form-select-input").on("input", function () {
        let parents = $(this).parents(".js-form-select");
        let value = $(this).val().toLowerCase();
        $(parents).find(".js-form-select-name").each(function (index, elem) {
            if ($(elem).text().toLowerCase().indexOf(value) > -1) {
                $(elem).show();
            } else {
                $(elem).hide();
            }
        });

        CompareValue($(this));

        if ($(this).hasClass('input-year-min') || $(this).hasClass('input-year-max')) {
            if ($(this).val().length > 3) {
                if ($(this).hasClass('input-year-max')) {
                    let minYear = $(this).data('year-min');
                    if ($(this).val() < minYear) {
                        $(this).addClass('is-error').css('color', 'rgb(255, 0, 0)');

                        return;
                    } else {
                        $(this).removeClass('is-error').css('color', '');
                    }
                }
                if (timer) {
                    clearTimeout(timer);
                }
                timer = setTimeout(function () {
                    updateTotalCars();
                }, 1000);
            }
        }


    });

    $(".js-check-select-close").on("click", function () {
        $(this).parents(".js-check-select").toggleClass("is-open");
    });

    $(".filter .check-select__drop-btn").on("click", function () {
        $(this).parents(".js-check-select").toggleClass("is-open");
    });


    /*SELECT MARK*/

    $(".js-tab-small-item").on("click", function () {
        let tab = $(this).data("tab");

        $(".js-tab-small-item").removeClass("is-active");
        $(this).addClass("is-active");

        $(".js-tab-small-block").removeClass("is-active");
        $(".js-tab-small-block[data-tab=" + tab + "]").addClass("is-active");
    });


    $(".js-mark .js-all").on("click", function () {
        var nameString = "Марка";
        var mark_count = 0;

        $(".js-mark input").each(function (index, elem) {
            $(elem).prop('checked', true);
            mark_count = mark_count + 1;

            if (mark_count == 1) {
                let name = $(elem).parents(".check__item").find(".check__label").text().trim();
                let id = $(elem).parents(".check__item").find(".check__label").data('id');
                nameString = $(elem).parents(".check__item").find(".check__label").text();
                $(".js-tab-small-item[data-tab=" + id + "]").addClass("is-show").addClass("is-active");
                $(".js-tab-small-block[data-tab=" + id + "]").addClass("is-show").addClass("is-active");
            } else {
                let name = $(elem).parents(".check__item").find(".check__label").text().trim();
                let id = $(elem).parents(".check__item").find(".check__label").data('id');
                $(".js-tab-small-item[data-tab=" + id + "]").addClass("is-show");
                $(".js-tab-small-block[data-tab=" + id + "]").addClass("is-show");
                nameString = nameString + "/" + $(elem).parents(".check__item").find(".check__label").text();
            }
        });

        nameString = nameString + "(" + mark_count + ")";
        $(".js-mark .js-check-select-main span").text(nameString);
        $(".js-model").removeClass("is-disabled")
        $(".js-mark").addClass("is-full");
    });

    $(".js-mark .check__item input").on("click", function () {
        clickOnMark()

    });

    function clickOnMark(withModels = true) {

        //рисует марку и модель в верхнем меню
        var nameString = "Марка";
        var mark_count = 0;
        var cheked_marks = [];

        $(".js-mark input").each(function (index, elem) {

            let name = $(elem).parents(".check__item").find(".check__label").text().trim();
            let id = $(elem).parents(".check__item").find(".check__label").data('id');

            if ($(elem).is(':checked')) {

                cheked_marks.push(id)
                mark_count = mark_count + 1;

                if (mark_count == 1) {

                    nameString = $(elem).parents(".check__item").find(".check__label").text();
                    $(".js-tab-small-item[data-tab=" + id + "]").addClass("is-show").addClass("is-active");
                    $(".js-tab-small-block[data-tab=" + id + "]").addClass("is-active");

                } else {

                    $(".js-tab-small-item[data-tab=" + id + "]").addClass("is-show");
                    nameString = nameString + "/" + $(elem).parents(".check__item").find(".check__label").text();
                }
            }

            if (!$(this).is(':checked')) {
                let id = $(this).parents(".check__item").find(".check__label").data('id');
                $(".js-tab-small-item[data-tab=" + id + "]").removeClass("is-show").removeClass("is-active");
                $(".js-tab-small-block[data-tab=" + id + "]").removeClass("is-active");
                $(".js-tab-small-block[data-tab=" + id + "]").find('input[type=checkbox]').each(function () {
                    this.checked = false;
                });
            }
        });


        if (mark_count != 0) {
            nameString = nameString + "(" + mark_count + ")";
            $(".js-model").removeClass("is-disabled")
            $(".js-mark").addClass("is-full");
        } else {
            $(".js-mark").removeClass("is-full");
            $(".js-model").addClass("is-disabled")
            $('div[data-name="Модель"]').parents(".js-check-select").removeClass("is-open");

        }
        $(".js-mark .js-check-select-main span").text(nameString);

        // let url = new URL(window.location.href);
        // url.searchParams.set('marks_ids', cheked_marks);
        // history.pushState("", "", url);


        if(withModels){
            setNameSelectModel()
        }
        // updateTotalCars();
    }

    // Отображает placeholder для select Марки и Модели
    clickOnMark(false);
    setNameSelectModel(false);

    $(".js-perPage").on("click", function (e) {
        e.preventDefault();
        let perPage = $(this).data('per-page');
        let url = new URL(window.location.href);
        let data = {};
        url.searchParams.set('perPage', perPage);

        $('.js-perPage').each(function () {
            $(this).removeClass('is-active')
        })
        $(this).addClass('is-active')

        let modelsIds = url.searchParams.get('models_ids');
        let marksIds = url.searchParams.get('marks_ids');
        if (marksIds) {
            data['marks_ids'] = marksIds;
        }
        if (modelsIds) {
            data['models_ids'] = modelsIds;
        }
        let category = $("#catalog-page").attr('data-category');

        if (category) {

            data['category'] = category
        }

        // Добавляем данные о странице, если они существуют
        let activePage = $('.is-active.pagination__item').data('page');
        if (activePage) {
            data['page'] = activePage;
        }
        if (perPage) {
            data['perPage'] = perPage;
        }
        updateCatalog(data)
        // window.location.href = url.href;
    });

    var status = 0;
    var cardTechItem = $(".card__tech div");

    /*определяем количество характеристик в карточке авто*/
    function cardTechCount() {
        /*если количество характеристик в карточке авто меньше или равно 6 то скрываем кнопку*/
        if (cardTechItem.length <= 6) {
            $(".js-card-more a").hide();
        }
    }

    cardTechCount()

    $(".js-card-more a").on("click", function () {

        if (status == 0) {
            $(".js-card-tech").addClass("is-active");
            $(this).text("Свернуть характеристики");
            status = 1;
        } else {
            $(".js-card-tech").removeClass("is-active");
            $(this).text("Больше характеристик");
            status = 0;
        }

        return false;
    });
    $(".js-catalog-sort").on("change", function () {
        let sort = $(this).val();
        let url = new URL(window.location.href);
        let data = {};
        url.searchParams.set('sort', sort);
        // history.pushState("", "", url);
        let modelsIds = url.searchParams.get('models_ids');
        let marksIds = url.searchParams.get('marks_ids');
        if (marksIds) {
            data = {'marks_ids': marksIds};
        }
        if (modelsIds) {
            data = {'models_ids': modelsIds};
        }
        let category = $("#catalog-page").attr('data-category');

        if (category) {
            data.category = category
        }
        updateCatalog(data)
        // window.location.href = url.href;
    });


    $(".js-view-catalog").on("click", function (e) {
        e.preventDefault();
        let view = $(this).data('view');
        let data = {};
        let url = new URL(window.location.href);
        url.searchParams.set('view', view);
        // history.pushState("", "", url);
        $('.js-view-catalog').each(function () {
            $(this).removeClass('is-active')
        })
        $(this).addClass('is-active')
        let modelsIds = url.searchParams.get('models_ids');
        let marksIds = url.searchParams.get('marks_ids');
        if (marksIds) {
            data['marks_ids'] = marksIds;
        }
        if (modelsIds) {
            data['models_ids'] = modelsIds;
        }
        let category = $("#catalog-page").attr('data-category');

        if (category) {

            data['category'] = category
        }

        // Добавляем данные о странице, если они существуют
        let activePage = $('.is-active.pagination__item').data('page');
        if (activePage) {
            data['page'] = activePage;
        }
        updateCatalog(data)
    })


    $('#hand_input input, #step2 input').on('input', function () {
        $(this).parents(".js-form-field").removeClass("is-error")
    })

    $('#hand_input select').on('change', function () {
        $(this).parents(".js-form-field").removeClass("is-error")
    })

    $("#step2 .js-phone").on('keyup', function () {
        $(this).parents(".js-form-field").removeClass("is-error")
    })


    $("#trade-in-form .js-next").on("click", function () {
        let count = 0;
        let parents = $(this).parents(".js-tab-block");

        parents.find("input").each(function (index, elem) {
            if (!$(elem).val()) {
                count = count + 1;
                $(elem).parents(".js-form-field").addClass("is-error")
            }

            if ($(elem).hasClass("js-vin") && $(elem).val().length < 17) {
                count = count + 1;
                $(elem).parents(".js-form-field").addClass("is-error");
            }
        });

        parents.find('select[name="gearbox"]').each(function (index, elem) {
            if (!$(elem).val()) {
                count = count + 1;
                $(elem).parents(".js-form-field").addClass("is-error")
            }
        });

        if (count == 0) {
            $(".js-step").addClass("is-last");
            $(".js-step-item").removeClass("is-active");
            $(".js-step-item[data-step='2']").addClass("is-active");
            $(".js-step-body").removeClass("is-active");
            $(".js-step-body[data-step='2']").addClass("is-active");
        } else {

        }

        return false;
    });

    $("#trade-in-form .js-prev").on("click", function () {

        $(".js-step").addClass("is-last");
        $(".js-step-item").removeClass("is-active");
        $(".js-step-item[data-step='1']").addClass("is-active");
        $(".js-step-body").removeClass("is-active");
        $(".js-step-body[data-step='1']").addClass("is-active");

    });

    // форма онлайн записи на сервис
    // Функция для проверки заполненности инпутов и селектов на текущем шаге
    function validateStep($step) {
        let isValid = true;

        // Находим инпуты и селекты в текущем шаге
        let $inputs = $step.find('input[type="text"], input[type="number"]');
        let $selects = $step.find('select');
        let $radios = $step.find('input[type="radio"]');
        let $textArea = $step.find('textarea');
        let $checkboxes = $step.find('input[type="checkbox"].aggree-check');

        if ($radios.length > 0) {
            let checked_radios = $step.find('input[type=radio]:checked');
            if (checked_radios.length > 0) {
                isValid = true;
                $step.find('.js-form-error').removeClass('is-error');
            } else {
                $step.find('.js-form-error').addClass('is-error');
                isValid = false;
                return false
            }
        }

        // Проверка чекбоксов
        if ($checkboxes.length > 0) {
            let checkedCheckboxes = $checkboxes.filter(':checked');
            if (checkedCheckboxes.length === 0) {
                isValid = false;
                $checkboxes.each(function () {
                    $(this).closest('.js-form-field').addClass('is-error');
                });
            } else {
                $checkboxes.each(function () {
                    $(this).closest('.js-form-field').removeClass('is-error');
                });
            }
        }

        // Если есть инпуты, проверяем их
        if ($inputs.length > 0) {
            $inputs.each(function () {
                if ($(this).attr('name') === 'mileage' && !$(this).hasClass('is-required')) {
                    return; // Переходим к следующему элементу
                }
                if ($(this).val().trim() === "") {
                    isValid = false;
                    $(this).closest('.js-form-field').addClass('is-error');
                } else {
                    $(this).closest('.js-form-field').removeClass('is-error');
                }
            });
        }

        // Если есть селекты, проверяем их
        if ($selects.length > 0) {
            $selects.each(function () {
                if ($(this).attr('name') === 'car_part' && !$(this).hasClass('is-required')) {
                    return; // Переходим к следующему элементу
                }
                if ($(this).val() === "") {
                    isValid = false;
                    $(this).closest('.js-form-field').addClass('is-error');
                } else {
                    $(this).closest('.js-form-field').removeClass('is-error');
                }
            });
        }

        if ($textArea.length > 0) {
            $textArea.each(function () {
                if ($(this).val() === "") {
                    isValid = false;
                    $(this).closest('.js-form-field').addClass('is-error');
                }else if ($(this).attr('data-limit') !== undefined) {
                    let maxLength = $(this).data('limit'); // Получаем значение лимита из атрибута data-limit
                    let textLength = $(this).val().length;
                    let errorElement = $(this).siblings('.form__error'); // Ищем элемент ошибки рядом с textarea
                    let wrapper = $(this).parents('.form__field');
                    if (textLength > maxLength) {
                        isValid = false;
                        errorElement.show(); // Показать сообщение об ошибке
                        wrapper.addClass('is-error')
                        errorElement.find('span').text(`Превышено максимальное количество символов ( ${textLength}/${maxLength} )`); // Изменить текст ошибки
                    }
                } else {
                    $(this).closest('.js-form-field').removeClass('is-error');
                }
            });
        }

        // Если нет ни инпутов, ни селектов на шаге, шаг считается валидным
        // if ($inputs.length === 0 && $selects.length === 0) {
        //     isValid = true;
        // }

        return isValid;
    }

    // Функция для обновления прогресс-бара
    function updateProgress(step) {
        const $stepControl = $('#zapis-form .step__control,#repair-consultation-form .step__control');
        $stepControl.removeClass('step-progress-25 step-progress-50 step-progress-75 step-progress-100');

        if (step === 1) {
            $stepControl.addClass('step-progress-25');
        } else if (step === 2) {
            $stepControl.addClass('step-progress-50');
        } else if (step === 3) {
            $stepControl.addClass('step-progress-75');
        } else if (step === 4) {
            $stepControl.addClass('step-progress-100');
        }
    }

    // Обработка клика на "Далее"
    $('#zapis-form .js-next, #repair-consultation-form .js-next').on('click', function (e) {
        e.preventDefault();

        let $currentStep = $(this).closest('.js-step-body');
        let currentStepIndex = $currentStep.data('step');

        // Проверка текущего шага
        if (validateStep($currentStep)) {
            if (currentStepIndex === 1) {
                let know_reason = $currentStep.find('input[type=radio]:checked');
                if (know_reason.length > 0 && know_reason.val() === "know") {
                    currentStepIndex = 3;
                }
            }
            // Переход на следующий шаг, если валидация успешна
            let $nextStep = $('.js-step-body[data-step="' + (currentStepIndex + 1) + '"]');
            $currentStep.removeClass('is-active');
            $nextStep.addClass('is-active');

            // Обновляем шаги в контроллере
            $('.js-step-item').removeClass('is-active');
            $('.js-step-item[data-step="' + (currentStepIndex + 1) + '"]').addClass('is-active');

            // Обновляем прогресс-бар
            updateProgress(currentStepIndex + 1);
        }
    });

    // Обработка клика на "Назад"
    $('#zapis-form .js-prev,#repair-consultation-form .js-prev').on('click', function (e) {
        e.preventDefault();

        if ($(this).closest('#step4.pin-class').length > 0) {
            $('.form-hide').show();
            $('.form-hide').removeClass('not__clear-phone');
            $('.verificationCodeContainer').hide();
            $('#zapis-form #step4').removeClass('pin-class');
            return; // Прерываем выполнение, если это элемент из #step4.pin-class
        }

        let $currentStep = $(this).closest('.js-step-body');
        let currentStepIndex = $currentStep.data('step');

        if (currentStepIndex === 4) {
            let know_reason = $(this).closest('form').find('input[name=know_reason]:checked');
            if (know_reason.length > 0 && know_reason.val() === "know") {
                currentStepIndex = 2;
            }
        }

        // Переход на предыдущий шаг
        let $prevStep = $('.js-step-body[data-step="' + (currentStepIndex - 1) + '"]');
        $currentStep.removeClass('is-active');
        $prevStep.addClass('is-active');

        // Обновляем шаги в контроллере
        $('.js-step-item').removeClass('is-active');
        $('.js-step-item[data-step="' + (currentStepIndex - 1) + '"]').addClass('is-active');

        // Обновляем прогресс-бар
        updateProgress(currentStepIndex - 1);
    });

    // Инициализация прогресса на первом шаге
    updateProgress(1);


    $(".js-tab-link").on("click", function () {
        let tab = $(this).data("tab");

        $(".js-tab-link").removeClass("is-active");
        $(this).addClass("is-active");

        $(".js-tab-name").text($(this).text());
        $(".js-tab-control").removeClass("is-open");

        $(".js-tab-block").removeClass("is-active");
        $(".js-tab-block[data-tab=" + tab + "]").addClass("is-active");
    });

    $(".manually").on("click", function () {

        $(".js-tab-link[data-tab='1']").removeClass("is-active");

        $(".js-tab-link[data-tab='2']").addClass("is-active");

        $(".js-tab-block[data-tab='1']").removeClass("is-active");

        $(".js-tab-block[data-tab='2']").addClass("is-active");

    });

    $(".js-buy-more").on("click", function () {
        $(this).toggleClass("is-active");

        if ($(this).hasClass("is-active")) {
            $(this).find("span").text("Свернуть");
            $(".js-buy-form").toggleClass("is-active");
            $(".js-buy-form .is-hidden-row").fadeIn(300, function () {
            });
        } else {
            $(this).find("span").text("Больше параметров");
            $(".js-buy-form").toggleClass("is-active");
            $(".js-buy-form .is-hidden-row").fadeOut(300, function () {
            });
        }
    });

    /*$(".js-number").bind("change keyup keydown input click", function() {
        if (this.value.match(/[^0-9]/g)) {
            this.value = this.value.replace(/[^0-9]/g, '');
            this.value = this.value;
        }
    });*/

    $(".js-number").on("input", function () {
        const input = this;

        // Убираем фокус перед заменой значения
        input.blur();

        // Удаляем нецифровые символы, кроме пробелов
        input.value = input.value.replace(/[^0-9\s]/g, '');

        // Возвращаем фокус к элементу после обновления
        input.focus();
    });

    $(".js-select").styler();

    $(".js-m-city").on("click", function () {
        $(".js-m-city-dop").addClass("is-active");
    });

    $(".js-m-city-back").on("click", function () {
        $(".js-m-city-dop").removeClass("is-active");
    });

    /*$(".js-mobile-menu-item").on("click", function () {
        $(this).next(".js-mobile-menu-dop").addClass("is-active");

        return false;
    });*/

    /*календарь в попапе онлайн записи*/
    // $(document).find('#salon-date').datetimepicker({
    //     minDate: 0,
    //     dayOfWeekStart: 1,
    //     format:'d.m.Y',
    //     timepicker:false,
    //     onSelectDate:function(ct,$i){
    //     }
    // });
    // $.datetimepicker.setLocale('ru');


    // При клике мимо попапа закрываем и очищаем форму если нужно.
    $(document).on("click", function (e) {
        const popup = $(".js-popup");
        const resetFormIDS = ["zapis-form", "repair-consultation-form"];

        if (!popup.is(e.target)) return;

        popup.removeClass("is-open");
        $("body").removeClass("is-hidden");
        $(".js-form-ok").removeClass("is-active");

        // Функция для очистки инпутов и select-ов
        function clearInputsAndErrors(form) {
            let inputsToClear;
            const checkboxes = form.find("input:checkbox, input:radio");
            const selectsToClear = form.find("select");

            // Исключаем input с phone, name, checkbox, radio
            if (window.user){
                inputsToClear = form.find("input:not([type='checkbox'],[type='hidden'], [type='radio'], [name='phone'], [name='name'], [name='email'])")
                    .not("[aria-hidden='true']")
                    .not("[name^='my_name']")
                    .not("[name='valid_from']")
                    .filter(function() {
                        return $(this).css("display") !== "none";
                    });
            }
            else {
                inputsToClear = form.find("input:not([type='checkbox'],[type='hidden']")
                    .not("[aria-hidden='true']")
                    .not("[name^='my_name']")
                    .not("[name='valid_from']")
                    .filter(function() {
                        return $(this).css("display") !== "none";
                    });;
            }


            // Очищаем значения
            inputsToClear.val('');
            checkboxes.prop('checked', false);
            selectsToClear.val('').each(function() {
                $(this).parent().find('.jq-selectbox__select-text').text($(this).attr('data-placeholder'));
            });

            // Удаляем фокус и классы ошибок
            inputsToClear.blur().parents(".js-form-field").removeClass("is-error");
            selectsToClear.blur().parents(".js-form-field").removeClass("is-error");
            checkboxes.parents(".js-form-field").removeClass("is-error");


            // Перезагружаем стили у select-ов (если используется плагин)
            selectsToClear.styler('destroy').styler();
        }

        // Если существует #trade-in-form
        const tradeInForm = $("#trade-in-form");
        if (tradeInForm.length > 0) {
            clearInputsAndErrors(tradeInForm);
            $(".js-step").addClass("is-last");
            $(".js-step-item").removeClass("is-active");
            $(".js-step-item[data-step='1']").addClass("is-active");
            $(".js-step-body").removeClass("is-active");
            $(".js-step-body[data-step='1']").addClass("is-active");
        }

        // Проверяем формы из resetFormIDS которые нужно очистить
        popup.find("form").each(function () {
            if (!resetFormIDS.includes(this.id)) return;

            this.reset(); // Сбрасываем стандартное состояние формы
            clearInputsAndErrors($(this)); // Дополнительная очистка для select2 и других кастомных элементов

            // Применяем действия для каждого элемента в списке select
            ["salons-serv", "salons-sity", "salons-serv-center", "salons-time"].forEach(name => {
                $(`select[name="${name}"]`).parent().find('.jq-selectbox__select-text')
                    .text($(`select[name="${name}"]`).attr('data-placeholder'));
            });

            $('#service-select, #salons-serv-center').val(null).trigger('change');
        });

        // Устанавливаем активные классы для step
        $(".js-step-item").removeClass("is-active");
        $(".js-step-item[data-step='1']").addClass("is-active");
        $(".js-step-body").removeClass("is-active");
        $(".js-step-body[data-step='1']").addClass("is-active");
    });

    $(".js-popup-close").on("click", function () {
        $("body").removeClass("is-hidden");
        $(this).parents(".js-popup").removeClass("is-open");
        $(this).parents(".js-popup").removeClass("is-ok");
    });

    $(".js-popup-close").on("click", function () {
        const resetFormIDS = ['zapis-form','repair-consultation-form','trade-in-form']
        let inputsToClear;
        // Проверяем наличие элемента с классом #trade-in-form
        if ($("#trade-in-form").length > 0) {
            // Находим все инпуты внутри родительского блока, который нужно очистить
            let form = $("#trade-in-form");
            if (window.user){
                inputsToClear = form.find("input:not([type='checkbox'],[type='hidden'], [type='radio'], [name='phone'], [name='name'], [name='email'])")
                    .not("[aria-hidden='true']")
                    .not("[name^='my_name']")
                    .not("[name='valid_from']")
                    .filter(function() {
                        return $(this).css("display") !== "none";
                    });
            }
            else {
                inputsToClear = form.find("input")
                    .not("[aria-hidden='true']")
                    .not("[name^='my_name']")
                    .not("[name='valid_from']")
                    .filter(function() {
                        return $(this).css("display") !== "none";
                    });
            }
            let selectsToClear = form.find("select");
            // Очищаем значения в найденных инпутах, исключая элементы с типом "checkbox"
            inputsToClear.each(function () {
                if ($(this).attr('type') !== 'checkbox') {
                    $(this).val('');
                }
            });

            $('select[name="gearbox"]').val('')
            $('select[name="gearbox"]').parent().find('.jq-selectbox__select-text').text($('select[name="gearbox"]').attr('data-placeholder'))

            // Удаляем фокус с инпутов
            inputsToClear.blur();

            // Удаляем классы ошибок
            inputsToClear.parents(".js-form-field").removeClass("is-error");
            $('select[name="gearbox"]').parents(".js-form-field").removeClass("is-error");

            // Выполняем дополнительные действия
            $(".js-step").addClass("is-last");
            $(".js-step-item").removeClass("is-active");
            $(".js-step-item[data-step='1']").addClass("is-active");
            $(".js-step-body").removeClass("is-active");
            $(".js-step-body[data-step='1']").addClass("is-active");
        }

        // Проверяем наличие элемента с классом #zapis-form
        if ($("#zapis-form").length > 0 || $('#repair-consultation-form').length > 0) {
            let form = $(this).parents('.popup').find('form');
            form.each(function () {
                if (!resetFormIDS.includes(this.id)) return;
                // Сбрасываем форму
                this.reset();

                // Для дополнительного сброса значений (например, у select2 или других кастомных элементов)
                $(this).find('input, textarea, select').not(":radio, :checkbox, [name='phone'], [name='name'], [name='email']").val('');
                $(this).find('input:radio').prop('checked', false);

                // Находим все инпуты внутри родительского блока, который нужно очистить

                if (window.user){
                    inputsToClear = form.find("input:not([type='checkbox'],[type='hidden'], [type='radio'], [name='phone'], [name='name'], [name='email'])")
                        .not("[aria-hidden='true']")
                        .not("[name^='my_name']")
                        .not("[name='valid_from']")
                        .filter(function() {
                            return $(this).css("display") !== "none";
                        });
                }
                else {
                    inputsToClear = form.find("input")
                        .not("[aria-hidden='true']")
                        .not("[name^='my_name']")
                        .not("[name='valid_from']")
                        .filter(function() {
                            return $(this).css("display") !== "none";
                        });
                }
                let selectsToClear = form.find("select");

                // Очищаем значения в найденных инпутах, исключая элементы с типом "checkbox"
                // inputsToClear.each(function () {
                //     if ($(this).attr('type') !== 'checkbox') {
                //         $(this).val('');
                //     }
                // });

                $('select[name="salons-serv"]').parent().find('.jq-selectbox__select-text').text($('select[name="salons-serv"]').attr('data-placeholder'));

                $('select[name="salons-sity"]').parent().find('.jq-selectbox__select-text').text($('select[name="salons-sity"]').attr('data-placeholder'));

                $('select[name="salons-serv-center"]').parent().find('.jq-selectbox__select-text').text($('select[name="salons-serv-center"]').attr('data-placeholder'));

                $('select[name="salons-time"]').parent().find('.jq-selectbox__select-text').text($('select[name="salons-time"]').attr('data-placeholder'));

                $('#service-select').val(null).trigger('change');

                $('#salons-serv-center').val(null).trigger('change');

                // Удаляем фокус с инпутов
                inputsToClear.blur();
                selectsToClear.styler('destroy');
                selectsToClear.styler();

                // Удаляем классы ошибок
                inputsToClear.parents(".js-form-field").removeClass("is-error");
                selectsToClear.parents(".js-form-field").removeClass("is-error");
            });

            // Выполняем дополнительные действия
            $(".js-step-item").removeClass("is-active");
            $(".js-step-item[data-step='1']").addClass("is-active");
            $(".js-step-body").removeClass("is-active");
            $(".js-step-body[data-step='1']").addClass("is-active");
        }
    });

    $('.js-form-input[name="consult-mark"]').on('input', function () {
        var value = $(this).val();

        // Разрешаем только буквы русского и английского алфавита и пробелы
        var filteredValue = value.replace(/[^a-zA-Zа-яА-Я\s]/g, '');

        // Ограничиваем длину до 100 символов
        if (filteredValue.length > 100) {
            filteredValue = filteredValue.substring(0, 100);
        }

        // Устанавливаем отфильтрованное значение обратно в поле
        $(this).val(filteredValue);
    });

    $('.js-form-input[name="consult-model"]').on('input', function () {
        var value = $(this).val();

        // Разрешаем только буквы русского и английского алфавита и пробелы
        var filteredValue = value.replace(/[^a-zA-Zа-яА-ЯёЁ\s0-9]/g, '');

        // Ограничиваем длину до 100 символов
        if (filteredValue.length > 100) {
            filteredValue = filteredValue.substring(0, 100);
        }

        // Устанавливаем отфильтрованное значение обратно в поле
        $(this).val(filteredValue);
    });

    $(".js-for-card").slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        arrows: true,
        fade: true,
        dots: true,
        dotsClass: 'custom_paging',
        customPaging: function (slider, i) {
            return "<span class='pag'>" + (i + 1) + "</span>" + '/' + slider.slideCount;
        },
        prevArrow: "<button type='button' class='slick-prev pull-left'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\</div>\
        </button>",
        nextArrow: "<button type='button' class='slick-next pull-right'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </button>",
        responsive: [{
            breakpoint: 768,

            settings: {
                fade: false,
                slidesToShow: 2,
                variableWidth: true,
                arrows: false
            }
        }]
    });

    $(".js-item-slider").slick({
        slidesToShow: 3,
        slidesToScroll: 1,
        arrows: true,
        prevArrow: "<button type='button' class='slick-prev pull-left'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\</div>\
        </button>",
        nextArrow: "<button type='button' class='slick-next pull-right'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </button>",
        responsive: [{
            breakpoint: 1200,

            settings: {
                slidesToShow: 2,
                slidesToScroll: 2
            }
        }, {
            breakpoint: 768,

            settings: {
                slidesToShow: 2,
                arrows: false,
                variableWidth: true
            }
        }]
    });

    $(".js-stock-slider").not('.slick-initialized').slick({
        slidesToShow: 2,
        slidesToScroll: 1,
        arrows: true,
        prevArrow: "<button type='button' class='slick-prev pull-left'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\</div>\
        </button>",
        nextArrow: "<button type='button' class='slick-next pull-right'>\
        <svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </button>",
        responsive: [{
            breakpoint: 768,

            settings: {
                slidesToShow: 2,
                arrows: false,
                variableWidth: true
            }
        }]
    });
    $(".filter__tag a").on("click", function (e) {

        e.preventDefault();

        if ($(this).hasClass('is-active')) {
            return;
        }

        $(".filter__tag a").each(function (index, elem) {
            $(elem).removeClass()
        });
        $(this).addClass('is-active')

        let index = $(this).attr('href').lastIndexOf("/")
        let category = $(this).attr('href').slice(index + 1)
        if (category == 'catalog') {
            category = ""
        }

        let categoryTitle = $(this).data("title");
        resetSelectMark();
        resetSelectModel();
        // $('.js-category-title').text(categoryTitle);
        // document.title = categoryTitle;
        let array = {'category': category};
        $("#catalog-page").attr('data-category', category)
        clearErrorMessages();
        updateTotalCars(null, {'category': category})
        // updateUrl(category);
    });

    function updateCategory(res, withMarks = true) {
        //вставить новые марки, изменить плэйсхолдеры
        if (withMarks) {
            $('#marks').html(res.marks_html);
            $(".js-mark .check__item input").on("click", function () {
                clickOnMark()
            });
        }
        $(".input-year-min").attr('placeholder', "Год от " + (res.filters.min_year > 0 ? res.filters.min_year : ""))
        $(".input-year-max").attr('placeholder', "До " + (res.filters.max_year > 0 ? res.filters.max_year : ""))
        $(".input-milage-min").attr('placeholder', "Пробег от " + res.filters.min_mileage_formatted + " км")
        $(".input-milage-max").attr('placeholder', "До " + res.filters.max_mileage_formatted + " км")
        $(".input-price-min").attr('placeholder', "Цена от " + res.filters.min_price_formatted)
        $(".input-price-max").attr('placeholder', "До " + res.filters.max_price_formatted)

        $(".input-year-min").attr('data-year-min', (res.filters.min_year > 0 ? res.filters.min_year : null))
        $(".input-year-max").attr('data-year-min', (res.filters.min_year > 0 ? res.filters.min_year : null))
        insertYearSelect(res.filters.years)
        insertSelect(res.filters.car_body, 'car_body')
        insertSelect(res.filters.driving_gear_type, 'driving_gear_type')
        insertSelect(res.filters.engine_type, 'engine_type')
        insertSelect(res.filters.gearbox, 'gearbox')
        Inputmask().remove();
        Inputmask({
            autocomplete: "off",
            showMaskOnHover: false,
            showMaskOnFocus: false,
        }).mask(document.querySelectorAll("input"));
        // Inputmask().mask(document.querySelectorAll("input:not(.input-price-min):not(.input-price-max):not(.input-milage-min):not(.input-milage-max)"));


        compareAfterUpdateCategory()


    }


    function insertYearSelect(years) {
        if (!years) {
            return
        }
        let dropDownMinYears = $('.year-min-container');
        let dropDownMaxYears = $('.year-max-container');
        dropDownMinYears.empty();
        dropDownMaxYears.empty();
        dropDownMinYears.append($('<div >', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name year-min'
        }));
        dropDownMaxYears.append($('<div >', {
            'text': 'Любой',
            'class': 'form-select__drop-item js-form-select-name year-max'
        }));
        years.map((i) => {
            dropDownMinYears.append($('<div >', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name year-min'
            }));
            dropDownMaxYears.append($('<div >', {
                'text': i,
                'class': 'form-select__drop-item js-form-select-name year-max'
            }));
        })

        $(".year-min").on("click", function () {
            setSelectFormValue($(this));
        });
        $(".year-max").on("click", function () {
            setSelectFormValue($(this));
        });
    }

    function insertSelect(models, type) {
        let $select_template = $(`[data-select="${type}"]`);
        let select_list_template = $select_template.find('.form-select__drop');
        select_list_template.empty();
        select_list_template.append($('<div >', {
            'text': 'Любой', 'class': 'form-select__drop-item js-form-select-name'
        }));
        models.map((item) => {
            select_list_template.append($('<div >', {
                'text': item.title,
                'class': `form-select__drop-item js-form-select-name ${item.isActive ? "" : "__hide"}`,
                'data-id': item.id
            }));
        })

        $(".js-form-select-name").unbind('click').on("click", function () {
            setSelectFormValue($(this));
        });
    }

    $(".reset__filters").on("click", function (e) {
        e.preventDefault()
        resetFilters();
    })

    function resetFilters(){
        $(".form-select__main").each(function (index, elem) {
            $(this).find(".js-form-select-input").val('');
            $(this).find(".js-form-select-input:hidden").val('');

        })


        $('.js-form-select-input').val('');

        $(".f-buy__list-item").each(function (index, elem) {
            $(this).find("input").val('');
        })

        $("#marks input").each(function (index, elem) {
            this.checked = false;
        })

        $(".tab-small input").each(function (index, elem) {
            this.checked = false;
        })


        $(".js-mark .js-check-select-main span").text('Марка')

        // history.pushState("", "", "/catalog");
        $('.js-form-select').removeClass('is-full');
        clearErrorMessages();
        resetSelectMark();
        resetSelectModel();
        updateTotalCars();
    }

    $(".catalog-reset").on("click", function (e) {
        e.preventDefault()
        resetFilters();

    })

    function clearErrorMessages() {
        $('.error-validation').empty()
        $(".input-year-min").css('color', '');
        $(".input-year-max").css('color', '');
        $(".input-milage-min").css('color', '');
        $(".input-milage-max").css('color', '');
        $(".input-price-min").css('color', '');
        $(".input-price-max").css('color', '');
        $(".input-value-min").css('color', '');
        $('.input-value-max').css('color', '');
    }

    function resetSelectMark() {
        $(".js-mark .js-check-select-main span").text('Марка')
        $(".js-mark").removeClass("is-open").removeClass("is-full")
        $(".js-mark input").each(function (index, elem) {
            this.checked = false;
        })
    }

    function resetSelectModel() {

        $(".js-model .js-check-select-main span").text('Модель')
        $(".js-model").addClass("is-disabled")
        $(".js-model").removeClass("is-open")

        $(".js-model .js-tab-small-block").each(function (index, elem) {
            $(this).removeClass("is-active");
            $(elem).find("input").each(function (index, elem) {
                this.checked = false;
            })
        })

        $('.js-model .js-tab-small-item').each(function () {
            $(this).removeClass("is-show").removeClass("is-active");
        })
    }

    /*блок с марками аавто под фильтрацией показать еще*/

    function modelBlock() {
        // Изначально показываем первые 15 элементов списка
        var $listItems = $(".list-section ul");
        var $loadMoreBtn = $("#loadMoreCars");
        var $hideBtn = $("#hiddencarsbtn");

        var itemsToShow = window.innerWidth > 600 ? 15 : 14;

        function updateListDisplay() {
            $listItems.hide(); // Скрыть все элементы
            $listItems.slice(0, itemsToShow).show();

            if ($listItems.length <= itemsToShow) {
                $loadMoreBtn.hide();
                $hideBtn.hide();
            } else {
                $loadMoreBtn.show();
                $hideBtn.hide();
            }
        }

        updateListDisplay();

        // Обработчик клика по кнопке "Загрузить больше"
        $loadMoreBtn.on("click", function (e) {
            e.preventDefault();

            $listItems.filter(":hidden").slideDown();

            // Меняем класс кнопок
            $loadMoreBtn.addClass("noContent-more");
            $hideBtn.addClass("visible-more");
        });

        // Обработчик клика по кнопке "Скрыть"
        $hideBtn.on("click", function (e) {
            e.preventDefault();

            updateListDisplay();

            // Меняем класс кнопок обратно
            $hideBtn.removeClass("visible-more");
            $loadMoreBtn.removeClass("noContent-more");
        });

        $(window).resize(function () {
            itemsToShow = window.innerWidth > 600 ? 15 : 14;
            updateListDisplay();
        });
    }

    modelBlock();

    $('#repair-consultation-form').submit(function (e) {
        e.preventDefault();
        let validated = validateStep($(this).find('.js-step-body').last())
        if (!validated) {
            return
        }
        let form_wrapper = $(this);
        let route = $(this).data('route');
        let data = new FormData(e.target);
        let inpBlurOff = $(this).find("input");
        data.append('from_url', window.location.href)
        var $form = $(this);
        let salonId = $form.data('salon-id');
        if (salonId){
            data.append('salon_id', salonId);
        }
        var $submitButton = $form.find('button[type="submit"]');

        // Проверка на наличие файлов
        let fileInputs = $(form).find('input[type="file"]');
        fileInputs.each(function () {
            let files = this.files;
            if (files.length > 0) {
                for (let i = 0; i < files.length; i++) {
                    // Добавляем файлы в FormData
                    data.append(this.name, files[i]);
                }
            }
        });
        // // Проверка содержимого FormData
        // for (let [key, value] of data.entries()) {
        // }

        // Проверка флага, чтобы убедиться, что форма не отправляется повторно
        if ($form.data('isSubmitting')) return;
        // Устанавливаем флаг, что форма отправляется
        $form.data('isSubmitting', true);
        // Отключаем кнопку submit, чтобы предотвратить повторные нажатия
        $submitButton.prop('disabled', true);

        $.ajax({
            method: 'post',
            processData: false,
            contentType: false,
            cache: false,
            enctype: 'multipart/form-data',
            url: $(this).attr('action'),
            data: data,
            success: function (response) {
                $(".js-popup").addClass("is-ok");
                $("body").removeClass("is-hidden");
                resetFormState()


                setTimeout(function () {
                    $(".js-popup").removeClass("is-open");
                }, 2500);

                setTimeout(function () {
                    $(".js-popup").removeClass("is-ok");
                    form_wrapper[0].reset();
                    $('#service-select').val(null).trigger('change');
                    $('#salons-serv-center').val(null).trigger('change');
                    $('.js-select').styler('destroy'); // Удаление старого стиля
                    $('.js-select').styler(); // Применение стиля заново
                    inpBlurOff.blur();
                    $('#preview').empty();
                    $(".js-step").addClass("is-last");
                    $(".js-step-item").removeClass("is-active");
                    $(".js-step-item[data-step='1']").addClass("is-active");
                    $(".js-step-body").removeClass("is-active");
                    $(".js-step-body[data-step='1']").addClass("is-active");
                }, 3000);
            },
            error: function (response) {
                resetFormState()
                $.each(response.responseJSON.errors, function (field_name, error) {
                    form_wrapper.find('[name=' + field_name + ']')
                        .parents(".js-form-field")
                        .addClass('is-error')
                        .find(".form__error span")
                        .html(error)
                    form_wrapper.find('[name=' + field_name + ']')
                })

            }
        });

        function resetFormState() {
            $form.data('isSubmitting', false); // Сбрасываем флаг отправки
            $submitButton.prop('disabled', false); // Включаем кнопку обратно
        }
    });


});
