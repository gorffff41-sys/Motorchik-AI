import {popup} from "./popup.js";
import {PhoneVerification} from "./phoneVerification.js"
window.popup = popup;

document.addEventListener('DOMContentLoaded', () => {
    const observer = lozad('.lozad', {
        rootMargin: '100px 0px', // Загружаем заранее
        loaded: function(el) {
            el.classList.add('loaded'); // Для анимации
        }
    });
    observer.observe();
    $(document).ajaxComplete(function() {
        observer.observe();
    });
});

function _defineProperty(obj, key, value) {
    if (key in obj) {
        Object.defineProperty(obj, key, {value: value, enumerable: true, configurable: true, writable: true});
    } else {
        obj[key] = value;
    }
    return obj;
}

$.ajaxSetup({
    headers: {
        'X-CSRF-TOKEN': $("[name='csrf-token']").attr('content'),
    }
});

$.fn.select2.defaults.set('language', 'ru');

$(document).ready(function () {
    $.fn.slick.defaults = {
        prevArrow: "<button type='button' class='slick-prev pull-left'>" +
            "<svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'>" +
            "<use xlink:href='#svg-arrow-left'></use></svg>" +
            "</button>",
        nextArrow: "<button type='button' class='slick-next pull-right'>" +
            "<svg width='10' height='17' viewBox='0 0 10 17' class='svg-icon'>" +
            "<use xlink:href='#svg-arrow-right'></use></svg>" +
            "</button>",
    };
    popup();

    const zapisPhoneVerification = new PhoneVerification({
        formSelector: '#zapis-form',
        codeContainerSelector: '.verificationCodeContainer',
        errorMessageSelector: '.form__error span',
        phoneSelector: '.js-phone',
        codeInputSelector: '.verificationCode',
        verifyButtonSelector: '.verifyCodeButton',
        maxAttempts: 5,
        cooldownTime: 60000,
    });

    $('.js-select-service-type').select2({
        placeholder: 'Услуга *',
        allowClear: true,
        dropdownAutoWidth: true,
        dropdownCssClass: 'custom-drop',
        language: {
            noResults: function (params) {
                return "Нет результатов";
            }
        },
        dropdownParent: $('.js-form-field .serv-sel')
    });

    $('.js-select-service').select2({
        placeholder: 'Сервисный центр *',
        allowClear: true,
        dropdownAutoWidth: true,
        dropdownCssClass: 'custom-drop',
        language: {
            noResults: function (params) {
                return "Нет результатов";
            }
        },
        dropdownParent: $('.js-form-field .centr-sel')
    });

    function getClickOrTouchHandler() {
        return 'ontouchstart' in document.documentElement ? 'touchstart' : 'click';
    }

    $(".js-mobile-menu-item .mobile-link__control").on(getClickOrTouchHandler(), function (e) {
        // e.preventDefault();
        $(this).parent().next(".js-mobile-menu-dop").addClass("is-active");

        return false;
    });

    $(".js-m-city").on(getClickOrTouchHandler(), function (e) {
        e.preventDefault();
        $(".js-m-city-dop").addClass("is-active");
    });

    $(".js-m-city-back").on(getClickOrTouchHandler(), function (e) {
        e.preventDefault();
        $(".js-m-city-dop").removeClass("is-active");
    });

    $(".js-mobile-menu-item").on(getClickOrTouchHandler(), function (e) {
        e.preventDefault();
        $(this).next(".js-mobile-menu-dop").addClass("is-active");

        return false;
    });

    $(".js-mobile-menu-back").on(getClickOrTouchHandler(), function (e) {
        e.preventDefault();
        $(".js-mobile-menu-dop").removeClass("is-active");
    });

    var _$$slick, _$$slick2, _$$slick3, _$$slick4, _$$slick5;

    if (typeof $.cookie('cookie') === 'undefined') { // Checks to see if the cookie exists
        $(".cookies").addClass("is-open");
    } else {
        $(".js-cookie").removeClass("is-open");
    }

    $(".cookies__btn .btn").on('click', function () {
        $(".cookies").removeClass("is-open");

        $.cookie('cookie', 'was', {
            expires: null, path: '/'
        });
        return false;
    });


    $(".js-card-com-more a").on("click", function () {
        if ($(this).text() == "Все опции") {
            $(".js-card-com").addClass("is-active");
            $(this).text("Свернуть опции");
            status = 1;
        } else {
            $(".js-card-com").removeClass("is-active");
            $(this).text("Все опции");
            status = 0;
        }

        return false;
    });

    $(".js-share-link").on("click", function () {
        var text = window.location.href;
        $(".js-copy-text").val(text);
        $(".js-copy-text").select();
        $(".js-share-text").addClass("is-active");
        document.execCommand('copy');
        setTimeout(function () {
            $(".js-share-text").removeClass("is-active");
        }, 1200);
    });

    $("#link-site").val($(location).attr("href"));

    $(".p-share__linkblock-text").text($(location).attr("href"));

    $(window).scroll(function () {
        if ($(window).scrollTop() == $(document).height() - $(window).height()) {
            $(".card-mobile").addClass("is-hidden-bottom");
            $(".js-btn-mobile").addClass("is-hidden");
        } else {
            $(".js-btn-mobile").removeClass("is-hidden");
            $(".card-mobile").removeClass("is-hidden-bottom");
        }
    });

    $(".js-file-rez").on('change', function (element) {
        var fileName = '';

        var size = this.files[0].size;

        if (1000000 > size) {
            if (element.target.value) fileName = element.target.value.split('\\').pop();
            $(".js-file-text").text(fileName);
            $(".js-upload-wrap").addClass("is-hidden");
            $(".js-upload-list__wrap").addClass("is-active");
            $(".upload-wrap-error").removeClass("is-active");
        } else {
            $(".upload-wrap-error").addClass("is-active");
        }
    });

    if ($(window).width() > 960) {
        $(".js-aria-aside").stick_in_parent({
            offset_top: 20
        });

        $(".js-sticky").stick_in_parent({
            offset_top: 20
        });
    }

    $(".js-img-small").on("click", function (e) {
        e.preventDefault();
        var anchor = $(this).data('item');
        $(".js-scroll-to").removeClass("is-active");
        $(this).addClass("is-active");
        $('html, body').stop().animate({
            scrollTop: $(".js-img-big[data-item=" + anchor + "]").offset().top - 60
        }, 800);
    });

    $(window).scroll(function () {
        if ($(window).scrollTop() > 300) {
            $(".js-up").addClass('is-active');
        } else {
            $(".js-up").removeClass('is-active');
        }
    });

    $(".js-up").on('click', function (e) {
        e.preventDefault();
        $('html, body').animate({scrollTop: 0}, '300');
    });

    if ($(window).width() < 960) {
        $(".js-filter-title").on("click", function (e) {
            $(this).next(".js-filter-body").addClass("is-active");
        });

        $(".js-filter-back").on("click", function (e) {
            $(".js-filter-body").removeClass("is-active");
        });
    }

    $(".js-password-toggle").on("click", function (e) {
        $(this).toggleClass("is-active");
        if ($(this).hasClass("is-active")) {
            $(this).parents(".js-form-field").find(".js-form-input").prop('type', 'text');
        } else {
            $(this).parents(".js-form-field").find(".js-form-input").prop('type', 'password');
        }
    });

    if ($(window).width() < 960) {
        $(".js-delivery-name").on("click", function (e) {
            $(this).toggleClass("is-active");
            $(this).next(".js-delivery-body").slideToggle(300, function () {
            });
        });
    }

    $(window).scroll(function () {

        $(".js-to-block").on("click", function (e) {
            e.preventDefault();
            var anchor = $(this).attr('href');
            $('html, body').stop().animate({
                scrollTop: $(anchor).offset().top - 20
            }, 800);
        });
    });

    $(window).scroll(function () {

        $(".js-scroll-block").each(function (index) {
            if ($(window).scrollTop() + 35 > $(this).offset().top) {
                var anchor = $(this).attr('id');
                $(".js-scroll-to").removeClass("is-active");
                $(".js-scroll-to[data-id=" + anchor + "]").addClass("is-active");
            }
        });
    });

    $(".js-scroll-to").on("click", function (e) {
        e.preventDefault();
        var anchor = $(this).attr('href');
        $(".js-scroll-to").removeClass("is-active");
        $(this).addClass("is-active");
        $('html, body').stop().animate({
            scrollTop: $(anchor).offset().top - 60
        }, 800);
    });

    $(".js-card-title").on("click", function () {
        $(this).parents(".js-card-block").toggleClass("is-active");

        if ($(this).parents(".js-card-block").hasClass("is-active")) {
            $(this).parents(".js-card-block").find(".js-card-body").slideDown(300, function () {
            });
        } else {
            $(this).parents(".js-card-block").find(".js-card-body").slideUp(300, function () {
            });
        }
    });

    /*** FORM ***/
    $(".js-form-label").on("click", function () {
        $(this).parents(".js-form-field").addClass("is-filled");
        $(this).parents(".js-form-field").find(".js-form-input").focus();
    });

    $(".js-form-input").on("focus", function () {
        if ($(this).val().length == 0) {
            $(this).parents(".js-form-field").addClass("is-filled");
        }
    });

    $(".js-form-input").on("blur", function () {
        if ($(this).val() == "+7(___)-___-__-__") {
            $(this).val("");
        }
        if ($(this).val().length == 0) {
            $(this).parents(".js-form-field").removeClass("is-filled");
        }
    });

    /*** END FORM ***/


    $(".js-tab-control-main").on("click", function () {
        $(".js-tab-control").toggleClass("is-open");
    });

    /*** FILTER ***/
    $(".js-filter-btn").on("click", function () {
        $(".js-filter").addClass("is-active");
        $("body").addClass("is-hidden");
        $(".main").addClass("is-back");
    });

    $(".js-filter-close").on("click", function () {
        $(".js-filter").removeClass("is-active");
        $("body").removeClass("is-hidden");
        $(".main").removeClass("is-back");
    });
    /*** END FILTER ***/

    $(".js-city").on("click", function () {
        $(".js-city-popup").addClass("is-open");
        $("body").addClass("is-hidden");
    });

    $(".js-city-close").on("click", function () {
        $(".js-city-popup").removeClass("is-open");
        $("body").removeClass("is-hidden");
    });

    $(".js-count").spinner({
        min: 5,
        max: 2500,
        step: 1,
        start: 1000
    });

    $(".js-stock-slider").slick({
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
                slidesToShow: 1,
                slidesToScroll: 1,
                arrows: false,
                variableWidth: true,
                infinite: true,
            }
        }]
    });

    $(".js-map__slider").slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        arrows: false,
        // variableWidth: true,
        infinite: false,
        adaptiveHeight: true,
        dots: true,
    });

    $(".js-range").slider({
        range: true,
        min: 0,
        max: 500,
        values: [75, 300],
        slide: function slide(event, ui) {
            $(".js-min").val(ui.values[0]);
            $(".js-max").val(ui.values[1]);
        }
    });

    $(".js-popup-close").on("click", function () {
        $(".js-popup").removeClass("is-open");
        $("body").removeClass("is-hidden");
    });

    if ($('#map').length) {
        var init = function init() {
            var myMap = new ymaps.Map("map", {
                center: [47.222996, 39.701466],
                zoom: 12
            });

            var myPlacemark = new ymaps.Placemark(myMap.getCenter(), {}, {
                iconLayout: 'default#image',
                iconImageHref: './images/common/marker.svg',
                iconImageSize: [281, 82],
                iconImageOffset: [-140, -82]
            });

            myMap.controls.remove('zoomControl');
            myMap.behaviors.disable('scrollZoom');
            myMap.behaviors.disable('drag');
            myMap.geoObjects.add(myPlacemark);
        };

        ymaps.ready(init);
    }

    if ($('#where-map').length) {

        var init = function init() {
            var myMap = new ymaps.Map("where-map", {
                center: [47.222996, 39.701466],
                zoom: 12
            });

            let objectManager = new ymaps.ObjectManager();

            myMap.geoObjects.add(objectManager);

            $.ajax({
                // В файле data.json заданы геометрия, опции и данные меток .
                url: "./data/data.json"
            }).done(function (data) {
                objectManager.add(data);
            });
        };

        ymaps.ready(init);
    }

    $(".js-hamburger").on("click", function () {
        $(".js-mobile-menu").toggleClass("is-active");
        $("body").addClass("is-hidden");
    });

    $(".js-ibanner").slick((_$$slick = {
        slidesToShow: 1,
        slidesToScroll: 1,
        infinite: true,
        dots: true,
        arrows: false,
        fade: true
    }, _defineProperty(_$$slick, "infinite", false), _defineProperty(_$$slick, "prevArrow", "<button type='button' class='slick-prev pull-left'>\
        <div class='slick-arrow__block'>\
        <div class='slick-arrow__back'><svg width='36' height='32' viewBox='0 0 36 32' class='svg-icon'><use xlink:href='#svg-arrow-back-small'></use></svg>\</div>\
        <svg  width='10' height='15' viewBox='0 0 10 15' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\
        </div></button>"), _defineProperty(_$$slick, "nextArrow", "<button type='button' class='slick-next pull-right'>\
        <div class='slick-arrow__block'>\
        <div class='slick-arrow__back'><svg width='36' height='32' viewBox='0 0 36 32' class='svg-icon'><use xlink:href='#svg-arrow-back-small'></use></svg>\</div>\
        <svg  width='10' height='15' viewBox='0 0 10 15' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </div></button>"), _$$slick));

    $(".js-detail-slider").slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        fade: true,
        dots: true,
        arrows: true,
        prevArrow: "<button type='button' class='slick-prev pull-left'>\
        <svg width='33' height='32' viewBox='0 0 33 32' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\</div>\
        </button>",
        nextArrow: "<button type='button' class='slick-next pull-right'>\
        <svg width='33' height='32' viewBox='0 0 33 32' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </button>"
    });

    $(".js-lates-slider").slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        fade: true,
        dots: true,
        arrows: false
    });

    $(".js-mreview-slider").slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        fade: true,
        dots: true,
        arrows: false
    });

    $(".js-parther-slider").slick((_$$slick2 = {
        slidesToShow: 3,
        slidesToScroll: 1,
        variableWidth: true,
        infinite: false,
        autoplay: false,
        dots: false,
        arrows: true
    }, _defineProperty(_$$slick2, "infinite", false), _defineProperty(_$$slick2, "prevArrow", "<button type='button' class='slick-prev pull-left'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-left-mini'></use></svg>\</div>\
        </button>"), _defineProperty(_$$slick2, "nextArrow", "<button type='button' class='slick-next pull-right'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-right-mini'></use></svg>\
        </button>"), _defineProperty(_$$slick2, "responsive", [{
        breakpoint: 1200,

        settings: {
            slidesToShow: 2,
            slidesToScroll: 1
        }
    }, {
        breakpoint: 960,

        settings: {
            slidesToShow: 3,
            arrows: false
        }
    }, {
        breakpoint: 640,

        settings: {
            slidesToShow: 2,
            arrows: false
        }
    }]), _$$slick2));

    $(".js-goods-slider").slick((_$$slick3 = {
        slidesToShow: 3,
        slidesToScroll: 1,
        variableWidth: true,
        infinite: false,
        autoplay: false,
        dots: false,
        arrows: true
    }, _defineProperty(_$$slick3, "infinite", false), _defineProperty(_$$slick3, "prevArrow", "<button type='button' class='slick-prev pull-left'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-left-mini'></use></svg>\</div>\
        </button>"), _defineProperty(_$$slick3, "nextArrow", "<button type='button' class='slick-next pull-right'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-right-mini'></use></svg>\
        </button>"), _defineProperty(_$$slick3, "responsive", [{
        breakpoint: 1200,

        settings: {
            slidesToShow: 2,
            slidesToScroll: 1
        }
    }, {
        breakpoint: 960,

        settings: {
            slidesToShow: 3,
            arrows: false
        }
    }, {
        breakpoint: 640,

        settings: {
            slidesToShow: 2,
            arrows: false
        }
    }]), _$$slick3));

    $(".js-goods-slider-main").slick((_$$slick4 = {
        slidesToShow: 4,
        slidesToScroll: 1,
        variableWidth: true,
        infinite: false,
        autoplay: false,
        dots: false,
        arrows: true
    }, _defineProperty(_$$slick4, "infinite", false), _defineProperty(_$$slick4, "prevArrow", "<button type='button' class='slick-prev pull-left'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-left-mini'></use></svg>\</div>\
        </button>"), _defineProperty(_$$slick4, "nextArrow", "<button type='button' class='slick-next pull-right'>\
        <svg width='14' height='14' viewBox='0 0 14 14' class='svg-icon'><use xlink:href='#svg-arrow-right-mini'></use></svg>\
        </button>"), _defineProperty(_$$slick4, "responsive", [{
        breakpoint: 1200,

        settings: {
            slidesToShow: 2,
            slidesToScroll: 1
        }
    }, {
        breakpoint: 960,

        settings: {
            infinite: true,
            centerMode: true,
            slidesToShow: 1,
            arrows: false
        }
    }, {
        breakpoint: 640,

        settings: {
            slidesToShow: 1,
            arrows: false
        }
    }]), _$$slick4));

    $(".js-catalog-item").slick((_$$slick5 = {
        slidesToShow: 4,
        slidesToScroll: 1,
        infinite: false,
        autoplay: false,
        dots: false,
        arrows: true
    }, _defineProperty(_$$slick5, "infinite", false), _defineProperty(_$$slick5, "prevArrow", "<button type='button' class='slick-prev pull-left'>\
        <svg width='33' height='32' viewBox='0 0 33 32' class='svg-icon'><use xlink:href='#svg-arrow-left'></use></svg>\</div>\
        </button>"), _defineProperty(_$$slick5, "nextArrow", "<button type='button' class='slick-next pull-right'>\
        <svg width='33' height='32' viewBox='0 0 33 32' class='svg-icon'><use xlink:href='#svg-arrow-right'></use></svg>\
        </button>"), _defineProperty(_$$slick5, "responsive", [{
        breakpoint: 1310,

        settings: {
            slidesToShow: 3
        }
    }, {
        breakpoint: 960,

        settings: {
            slidesToShow: 3,
            arrows: false
        }
    }, {
        breakpoint: 640,

        settings: {
            slidesToShow: 2,
            arrows: false
        }
    }]), _$$slick5));

    $(".js-search-input").on("input change", function () {
        if ($(this).val().length > 0) {
            $(".js-search").addClass("is-focus");
        } else {
            $(".js-search").removeClass("is-focus");
        }
    });

    $(".js-search-delete").on("click", function () {
        $(".js-search-input").val("");
        $(".js-search").removeClass("is-focus");
    });

    $(".js-search-btn").on("click", function () {
        $(".js-search").toggleClass("is-active");
        $("body").addClass("is-hidden");
    });

    $(".js-search-close").on("click", function () {
        $(".js-search").toggleClass("is-active");
        $("body").removeClass("is-hidden");
    });

    $(".js-form-ok-close").on("click", function () {
        $("body").removeClass("is-hidden");
        $(".js-form-ok").removeClass("is-active");
        $(".js-popup").removeClass("is-open");

        setTimeout(function () {
            $(".js-popup").removeClass("is-ok");
        }, 3000);
    });


    $('.js-phone').inputmask({
        mask: '+7 (X99) 999-99-99',
        showMaskOnHover: true,
        showMaskOnFocus: true,
        inputmode: 'numeric',
        definitions: {
          'X': {
            validator: '[0-6,9]',
            cardinality: 1,
            placeholder: '_'
          },
          '9': {
            validator: '[0-9]',
            cardinality: 1,
            placeholder: '_'
          }
        },
        clearIncomplete: true
    });


    $(".js-mobile-menu-close").on("click", function () {
        $(".js-mobile-menu").toggleClass("is-active");
        $("body").removeClass("is-hidden");
    });

    if ($('#map-big').length) {
        var init = function init() {
            var myMap = new ymaps.Map("map-big", {
                center: [47.229929, 39.621310],
                zoom: 18
            });

            var myPlacemark = new ymaps.Placemark(myMap.getCenter(), {}, {
                iconLayout: 'default#image',
                iconImageHref: './images/common/marker.svg',
                iconImageSize: [50, 60],
                iconImageOffset: [-25, -60]
            });

            var myPlacemark1 = new ymaps.Placemark([47.295986, 39.711959], {}, {
                iconLayout: 'default#image',
                iconImageHref: './images/common/marker.svg',
                iconImageSize: [50, 60],
                iconImageOffset: [-25, -60]
            });

            var myPlacemark2 = new ymaps.Placemark([47.229929, 39.621310], {}, {
                iconLayout: 'default#image',
                iconImageHref: './images/common/marker.svg',
                iconImageSize: [50, 60],
                iconImageOffset: [-25, -60]
            });

            myMap.controls.remove('zoomControl');
            myMap.behaviors.disable('scrollZoom');
            myMap.behaviors.disable('drag');
            myMap.geoObjects.add(myPlacemark);
            myMap.geoObjects.add(myPlacemark1);
            myMap.geoObjects.add(myPlacemark2);
        };

        ymaps.ready(init);
    }

    //поле имя
    $('input[name="name"]').on('input', function () {
        let value = $(this).val();

        value = value.replace(/[^\p{L}\s\-]/gu, '');

        value = value.substring(0, 100);

        $(this).val(value);
    });

    // поле фио в лк
    $('.form__field-data-name input[name="name"]').on('input', function () {
        let value = $(this).val();

        value = value.replace(/[^а-яёa-z\s\-]/giu, '');
        value = value.slice(0, 100);
        $(this).val(value);
    });

    //пробег
    const $mileageInput = $('input[name="mileage"]');

    $mileageInput.on('keydown', function (e) {
        const allowedKeys = [
            'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight',
            'Tab', 'Home', 'End'
        ];

        if (allowedKeys.includes(e.key)) return;

        // Разрешаем только цифры
        if (!/^\d$/.test(e.key)) {
            e.preventDefault();
        }
    });

    // Чистим всё, что не цифры — нужно для телефонов и вставки
    $mileageInput.on('input', function () {
        this.value = this.value.replace(/\D/g, '');
    });

    // Дополнительная проверка при вводе или копировании
    $('input[name="mileage"]').on('input', function () {
        var value = $(this).val().replace(/[^\d]/g, ''); // Убираем все, кроме цифр

        if (value !== '') {
            var intValue = parseInt(value, 10);
            // Проверяем, находится ли значение в пределах от 1 до 1000000
            if (intValue < 1 || intValue > 1000000) {
                $(this).val('');
            } else {
                var formattedValue = intValue.toLocaleString('en-US');
                formattedValue = formattedValue.replace(/,/g, ' ');
                $(this).val(formattedValue);
            }
        }
    });

    //обЪем двигателя
    $('input[name="engine_capacity"]').on('input', function () {
        var inputValue = $(this).val();

        // Очищаем введенное значение от всего, кроме цифр и разделителя (точки или запятой)
        var cleanedValue = inputValue.replace(/[^\d.,]/g, '');

        // Разрешаем только один разделитель (точку или запятую)
        cleanedValue = cleanedValue.replace(/([.,])(?=.*[.,])/g, '');

        // Ограничиваем количество знаков после разделителя до двух
        cleanedValue = limitDecimalDigits(cleanedValue, 2);

        // Проверяем, входит ли значение в диапазон
        if (isValidCapacityValue(cleanedValue)) {
            $(this).val(cleanedValue);
        } else {
            $(this).val('');
        }
    });

    function limitDecimalDigits(value, maxDigits) {
        var parts = value.split(/[.,]/);
        if (parts.length > 1) {
            parts[1] = parts[1].slice(0, maxDigits);
        }
        return parts.join('.');
    }

    function isValidCapacityValue(value) {
        var floatValue = parseFloat(value.replace(',', '.'));

        return !isNaN(floatValue) && floatValue >= 1.0 && floatValue <= 20.0;
    }

    //год выпуска
    $('input[name="year"]').on('input', function () {
        // Убираем всё, кроме цифр
        this.value = this.value.replace(/[^0-9]/g, '');

        // Ограничиваем длину до 4 символов
        if (this.value.length > 4) {
            this.value = this.value.slice(0, 4);
        }
    });


    $('input[name="year"]').on('input', function (e) {
        var inputValue = e.target.value;

        // Оставляем только цифры
        var numericValue = inputValue.replace(/\D/g, '');

        // Проверяем, если введено ровно 4 цифры
        if (numericValue.length === 4) {
            // Преобразуем значение в число
            var intValue = parseInt(numericValue, 10);

            // Проверяем, находится ли значение в пределах от 1970 до текущего года
            var currentYear = new Date().getFullYear();
            if (!isNaN(intValue) && intValue >= 1970 && intValue <= currentYear) {
                // Заполняем поле ввода отформатированным значением (если нужно)
                $(this).val(intValue);
            } else {
                // Очищаем поле ввода, если число не соответствует условиям
                $(this).val('');
            }
        }
    });

    $('input[name="year"]').on('blur', function () {
        var inputValue = $(this).val();

        // Очищаем поле, если меньше 4 цифр
        if (inputValue.length < 4) {
            $(this).val('');
        }
    });

    //модель
    $('input[name="model"]').on('input', function () {
        var inputValue = $(this).val();

        // Удаляем все символы, кроме цифр, букв (латиницы и кириллицы) и пробелов
        var sanitizedValue = inputValue.replace(/[^a-zA-Zа-яА-Я0-9\s]/g, '');

        // Ограничиваем длину значения 100 символами
        sanitizedValue = sanitizedValue.substring(0, 100);

        // Присваиваем очищенное значение обратно полю ввода
        $(this).val(sanitizedValue);
    });

    //марка
    $('input[name="mark"]').on('input', function () {
        var inputValue = $(this).val();

        // Удаляем цифры и специальные символы, оставляя только буквы и пробелы
        var sanitizedValue = inputValue.replace(/[^a-zA-Zа-яА-Я\s]/g, '');
        // Ограничиваем длину строки до 100 символов
        if (sanitizedValue.length > 100) {
            sanitizedValue = sanitizedValue.substring(0, 100);
        }

        // Присваиваем очищенное значение обратно полю ввода
        $(this).val(sanitizedValue);
    });

    //винкод
    $('input[name="vin"]').on('input', function () {
        $(this).val($(this).val().toUpperCase());
        var inputValue = $(this).val();

        // Удаляем специальные символы, буквы российского алфавита и символы О, I, Q
        var sanitizedValue = inputValue.replace(/[^A-HJ-NPR-Z0-9]/g, '');

        // Ограничиваем длину VIN-кода 17 символами
        if (sanitizedValue.length > 17) {
            sanitizedValue = sanitizedValue.slice(0, 17);
        }

        // Присваиваем очищенное значение обратно полю ввода
        $(this).val(sanitizedValue);
    });

    /*таб стр в лк*/
    $(".profile-mob-nav-top").on("click", function () {
        $(".profile-mob-nav").toggleClass("active-list");
    });

    $(".js-check-select-main").on("click", function () {
        let parents = $(this).parents(".js-check-select");
        parents.toggleClass("is-open");
        event.stopPropagation(); // Остановка распространения события клика
    });

    // Закрытие меню при клике вне его области
    $(document).on("click", function (event) {
        if (!$(event.target).closest('.js-check-select').length) {
            $(".js-check-select.is-open").removeClass("is-open");
        }
    });

    /*фильтры по услугам на стр сервисы*/
    $(".services__filter-item").on("click", function (e) {
        // Добавить/удалить класс активной вкладки
        $(".services__filter-item").removeClass("services__filter-active");
        $(this).addClass("services__filter-active");
    });


    function checkScreenWidth() {
        let iconMenu1 = document.querySelector('.bodymovinanim1');
        let iconMenu2 = document.querySelector('.bodymovinanim2');
        let iconMenu3 = document.querySelector('.bodymovinanim3');

        let mouseEnterHandler1;
        let mouseLeaveHandler1;
        let mouseEnterHandler2;
        let mouseLeaveHandler2;
        let mouseEnterHandler3;
        let mouseLeaveHandler3;

        if (iconMenu1 && iconMenu2 && iconMenu3 && window.innerWidth >= 1311) {
            let animationMenu1 = bodymovin.loadAnimation({
                container: iconMenu1,
                renderer: 'svg',
                loop: false,
                autoplay: false,
                path: "js/data1.json"
            });

            let animationMenu2 = bodymovin.loadAnimation({
                container: iconMenu2,
                renderer: 'svg',
                loop: false,
                autoplay: false,
                path: "js/data2.json"
            });

            let animationMenu3 = bodymovin.loadAnimation({
                container: iconMenu3,
                renderer: 'svg',
                loop: false,
                autoplay: false,
                path: "js/data3.json"
            });

            var directionMenu1 = 1;
            var directionMenu2 = 1;
            var directionMenu3 = 1;

            mouseEnterHandler1 = e => {
                animationMenu1.setDirection(directionMenu1);
                animationMenu1.play();
            };

            mouseLeaveHandler1 = e => {
                animationMenu1.setDirection(-directionMenu1);
                animationMenu1.play();
            };

            mouseEnterHandler2 = e => {
                animationMenu2.setDirection(directionMenu2);
                animationMenu2.play();
            };

            mouseLeaveHandler2 = e => {
                animationMenu2.setDirection(-directionMenu2);
                animationMenu2.play();
            };

            mouseEnterHandler3 = e => {
                animationMenu3.setDirection(directionMenu3);
                animationMenu3.play();
            };

            mouseLeaveHandler3 = e => {
                animationMenu3.setDirection(-directionMenu3);
                animationMenu3.play();
            };

            iconMenu1.addEventListener('mouseenter', mouseEnterHandler1);
            iconMenu1.addEventListener('mouseleave', mouseLeaveHandler1);

            iconMenu2.addEventListener('mouseenter', mouseEnterHandler2);
            iconMenu2.addEventListener('mouseleave', mouseLeaveHandler2);

            iconMenu3.addEventListener('mouseenter', mouseEnterHandler3);
            iconMenu3.addEventListener('mouseleave', mouseLeaveHandler3);
        } else {
            if (iconMenu1) {
                iconMenu1.removeEventListener('mouseenter', mouseEnterHandler1);
                iconMenu1.removeEventListener('mouseleave', mouseLeaveHandler1);
            }

            if (iconMenu2) {
                iconMenu2.removeEventListener('mouseenter', mouseEnterHandler2);
                iconMenu2.removeEventListener('mouseleave', mouseLeaveHandler2);
            }

            if (iconMenu3) {
                iconMenu3.removeEventListener('mouseenter', mouseEnterHandler3);
                iconMenu3.removeEventListener('mouseleave', mouseLeaveHandler3);
            }
        }
    }

    window.addEventListener('resize', checkScreenWidth);
    checkScreenWidth();

    $('.js-select-service-type').styler();
    $('.js-select-service-type,.js-select-cities').change(function () {
        var type = $('select.js-select-service-type option:selected').data('id');
        let city = $('select.js-select-cities option:selected').val();
        let $select2 = $('select.js-select-service');

        if (type !== "") {
            $.ajax({
                url: '/api/auto-services', // Замените на ваш URL
                method: 'GET',
                data: {type: type,city:city},
                success: function (response) {
                    $select2.empty(); // Очищаем второй select

                    $select2.append(new Option("", "", true, true));
                    // Добавляем новые опции
                    $.each(response, function (index, service) {
                        $select2.append(`<option data-id="${service.id}" value="${service.id}">${service.title}</option>`);
                    });

                    // Если вы используете jQuery.styler() для обновления стилей
                    $select2.trigger('refresh'); // Перезапускаем обновление плагина
                    $select2.styler('refresh'); // Перезапускаем обновление плагина
                }
            });
        } else {
            $select2.html('<option value=""></option>');
            $select2.trigger('refresh'); // Перезапускаем обновление плагина
            $select2.styler('refresh');
        }
    });

    $('.js-select-service-car-part').change(function () {
        let $closestForm = $(this).closest('form');
        let typeServiceId = $(this).find('option:selected').data('id');
        let $select2 = $closestForm.find('select.js-select-car-part');

        if (typeServiceId !== "") {
            $.ajax({
                url: '/api/car-parts', // Замените на ваш URL
                method: 'GET',
                data: {typeServiceId: typeServiceId},
                success: function (response) {
                    $select2.empty(); // Очищаем второй select

                    $select2.append(new Option("", "", true, true));
                    // Добавляем новые опции
                    $.each(response, function (index, service) {
                        $select2.append(`<option data-id="${service.id}" value="${service.title}">${service.title}</option>`);
                    });

                    // Если вы используете jQuery.styler() для обновления стилей
                    $select2.trigger('refresh'); // Перезапускаем обновление плагина
                    $select2.styler('refresh'); // Перезапускаем обновление плагина
                }
            });
        } else {
            $select2.html('<option value=""></option>');
            $select2.trigger('refresh'); // Перезапускаем обновление плагина
            $select2.styler('refresh');
        }
    });

    $('.js-select-marks').change(function () {
        let modelId = $(this).find('option:selected').data('id');
        let $closestForm = $(this).closest('form'); // Можно заменить на ближайший контейнер, например, $(this).closest('.form-container')
        let $selectModels = $closestForm.find('select.js-select-models')

        if (modelId !== "") {
            $.ajax({
                url: '/api/models', // Замените на ваш URL
                method: 'GET',
                data: {modelId: modelId},
                success: function (response) {
                    $selectModels.empty(); // Очищаем второй select

                    $selectModels.append(new Option("", "", true, true));
                    // Добавляем новые опции
                    $.each(response, function (index, service) {
                        $selectModels.append(`<option data-id="${service.id}" value="${service.title}">${service.title}</option>`);
                    });

                    // Если вы используете jQuery.styler() для обновления стилей
                    $selectModels.trigger('refresh'); // Перезапускаем обновление плагина
                    $selectModels.styler('refresh'); // Перезапускаем обновление плагина
                }
            });
        } else {
            $selectModels.html('<option value=""></option>');
            $selectModels.trigger('refresh'); // Перезапускаем обновление плагина
            $selectModels.styler('refresh');
        }
    });

    onSelectServiceType();
    function onSelectServiceType() {

        $('.js-select-service').change(function () {
            let serviceId = $('select.js-select-service').find(":selected").data('id');
            getTime(serviceId)
        });
    }

    var $allListTimeSlot;
    var x = 0;
    var $timeSelect = $('select.js-salons-time');

    function getTime(salonId) {

        if (salonId > 0) {
            $.ajax({
                url: '/api/timeslots',
                method: 'GET',
                data: {idSalon: salonId},
                dataType: "json",
                success: function (data) {
                    if (data.ERROR === "Y") {
                        $(document).find("#time_slot_list").replaceWith(
                            `<div class="form_agree" id="not_time_slot_list">
                                <div><button type="button" class="button">записаться на сервис</button></div>
                            </div>`
                        )
                    } else if (data.ERROR === "N") {

                        // $(document).find("#auto_to-thanks .text_thanks").empty();
                        // $(document).find("#auto_to-thanks .text_thanks").text("Вы записаны на обслуживание в ДЦ " + data.result_info.NAME + " " + data.result_info.CITY + " " + data.result_info.ADDRES)


                        var enabledDays = [];
                        $allListTimeSlot = data.result;
                        $.each(data.result, function (index, value) {
                            enabledDays[enabledDays.length] = value.FORMAT
                        });

                        $(document).find("#salon-date").datepicker({
                            dateFormat: 'dd.mm.yy',
                            onSelect: function (dateText, inst) {
                                $('#salon-date').parents('.form__field').addClass('is-filled');
                                var timestamp = new Date(dateText.split(".").reverse().join("/")).getTime();
                                let TimeGroupOptions = "";

                                timestamp = String(timestamp);
                                timestamp = timestamp.slice(0, 10);

                                $.each($allListTimeSlot, function (index, value) {
                                    if (dateText == value.FORMATTED_DATE) {
                                        if (typeof value === "undefined") {
                                        } else {
                                            // формируем список опций по группам утро, день, вечер
                                            $.each(value.SLOTS, function (indexSlot, valueSlot) {
                                                let $titleBlock = "";
                                                switch (indexSlot) {
                                                    case "UTRO":
                                                        $titleBlock = `Утро`;
                                                        break;
                                                    case "DEN":
                                                        $titleBlock = `День`;
                                                        break;
                                                    case "VECHER":
                                                        $titleBlock = `Вечер`;
                                                        break;
                                                }

                                                // Создаем список опций для текущего группы
                                                let $listSlot = "";
                                                $.each(valueSlot, function(itemSlot, valueItemSlot) {
                                                    $listSlot += `<option value='${valueItemSlot.FORMATTED_TIME}'>${valueItemSlot.FORMATTED_TIME}</option>`;
                                                });
                                                // Добавляем список опций в группу `Утро/День/Вечер`
                                                TimeGroupOptions += `<optgroup label='${$titleBlock}'>${$listSlot}</optgroup>`;
                                            });
                                        }
                                    }
                                });

                                $timeSelect.empty(); // Очищаем select для времени

                                $timeSelect.append(new Option("", ""));
                                // Добавляем новые опции
                                $timeSelect.append(TimeGroupOptions);

                                $timeSelect.trigger('refresh'); // Перезапускаем обновление плагина
                                $timeSelect.styler('refresh'); // Перезапускаем обновление плагина
                            },
                            onClose: function (e){
                            },
                            beforeShowDay: function (date) {
                                var cd = date.getDate() + '.' + (date.getMonth() + 1) + '.' + date.getFullYear();
                                return [$.inArray(cd, enabledDays) !== -1]
                            }
                        });
                    }
                }
            });
        }
    }

    $('.form__field').on("click", function (e) {
        $(this).removeClass('is-error');
    });

    $('[data-limit]').on('input', function() {
        let maxLength = $(this).data('limit'); // Получаем значение лимита из атрибута data-limit
        let textLength = $(this).val().length;
        let errorElement = $(this).siblings('.form__error'); // Ищем элемент ошибки рядом с textarea
        let wrapper = $(this).parents('.form__field');
        if (textLength > maxLength) {
            errorElement.show(); // Показать сообщение об ошибке
            wrapper.addClass('is-error')
            errorElement.find('span').text(`Превышено максимальное количество символов ( ${textLength}/${maxLength} )`); // Изменить текст ошибки
            // $(this).val($(this).val().substring(0, maxLength)); // Обрезать текст до значения лимита
            // setTimeout(function () {
            //     errorElement.hide();
            //     wrapper.removeClass('is-error');
            // }, 3000);
        } else if (textLength === 0) {
            wrapper.removeClass('is-error')
            errorElement.find('span').text('Нужно заполнить описание проблемы'); // Вернуть текст ошибки по умолчанию
            errorElement.hide(); // Скрыть сообщение об ошибке, если текст пустой
        } else {
            wrapper.removeClass('is-error')
            errorElement.find('span').text('Нужно заполнить описание проблемы');
            errorElement.hide(); // Скрыть сообщение об ошибке, если всё нормально
        }
    });


    $('.form__field-custom textarea').on('input', function() {
        $(this).css('height', 'auto'); // Сбрасываем высоту перед пересчетом
        $(this).css('height', this.scrollHeight + 'px'); // Устанавливаем новую высоту на основе содержимого
    });


    let maxFiles = 5; // Максимальное количество файлов
    let filesArray = []; // Храним загруженные файлы

    $(document).on('change', 'input[type="file"][name="photos[]"]', function(e) {
        e.preventDefault();
        const files = Array.from(this.files); // Преобразуем FileList в массив
        const remainingSlots = maxFiles - filesArray.length; // Сколько файлов еще можно добавить

        // Если количество новых файлов превышает доступные слоты, обрезаем массив
        if (files.length > remainingSlots) {
            files.splice(remainingSlots);
            // Показываем ошибку пользователю
            $(this).closest('.attach__photo-box').addClass('is-error');

            setTimeout(function() {
                $('.attach__photo-box').removeClass('is-error');
            }, 3000);
        }

        // Находим ближайший контейнер для превью
        let preview = $(this).closest('.attach__photo-box').find('.preview-box');

        // Добавляем только те файлы, которые помещаются в оставшиеся слоты
        files.forEach((file, i) => {
            if (filesArray.length >= maxFiles) return;

            if (file.type === 'application/pdf') {
                renderPDFIcon(file, preview);
            } else {
                renderImage(file, preview);
            }

            let reader = new FileReader();
            reader.onload = function(e) {
                filesArray.push(file);
                updateRemovePreviewHandlers();
                updateInputFiles();
            };
            reader.readAsDataURL(file);
        });
        updateInputFiles();
    });

    // Функция для отображения превью изображения
    function renderImage(file, preview) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const imgId = 'img-' + (filesArray.length + 1);
            const imgHtml = `
            <div class="preview-img" id="${imgId}">
                <img src="${e.target.result}" alt="photo">
                <button type="button" class="remove-img" data-id="${imgId}">&times;</button>
            </div>`;
            preview.append(imgHtml);
        };
        reader.readAsDataURL(file);
    }

    // Функция для отображения иконки PDF
    function renderPDFIcon(file, preview) {
        const imgId = 'img-' + (filesArray.length + 1);
        const fileName = file.name.length > 15 ? file.name.substring(0, 12) + '...' : file.name;
        const pdfIconHtml = `
        <div class="preview-img" id="${imgId}">
            <img src="/images/pdf-icon.png" alt="PDF icon" style="width: 50px; height: 50px;">
            <small>${fileName}</small>
            <button type="button" class="remove-img" data-id="${imgId}">&times;</button>
        </div>`;
        preview.append(pdfIconHtml);
    }

    function updateInputFiles() {
        const dataTransfer = new DataTransfer();
        filesArray.forEach((file) => dataTransfer.items.add(file));

        // Обновляем все input[type="file"] с одинаковым именем
        $('input[type="file"][name="photos[]"]').each(function() {
            this.files = dataTransfer.files;
        });
    }

    // Функция для обновления обработчиков удаления изображений
    function updateRemovePreviewHandlers() {
        $('.remove-img').off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const id = $(this).data('id');
            $('#' + id).remove();

            filesArray = filesArray.filter((f, index) => {
                return 'img-' + (index + 1) !== id;
            });

            $('.preview-img').each(function(index) {
                const newId = 'img-' + (index + 1);
                $(this).attr('id', newId);
                $(this).find('.remove-img').data('id', newId);
            });

            updateInputFiles();
        });
    }

    $('.js-popup-close').on('click', function() {
        clearAllPhotos(); // Очищаем фото, если нужно

        const $popup = $(this).closest('.js-popup');
        resetPopupForm($popup);
        $popup.removeClass('is-open');
        $popup.removeClass("is-ok");
        $("body").removeClass("is-hidden");
    });

    // Удаление всех загруженных фото при клике за пределами .popup__wrap
    $(document).on('click', function(e) {
        const $popup = $('.js-popup.is-open');

        if ($popup.length === 0) return;

        const popupWrap = $popup.find('.popup__wrap');

        // Проверяем, был ли клик за пределами .popup__wrap
        if (!popupWrap.is(e.target) && popupWrap.has(e.target).length === 0) {
            // Проверяем, что клик не был по элементу с классом .remove-img или его потомку
            if (!$(e.target).hasClass('remove-img') && !$(e.target).closest('.remove-img').length) {
                clearAllPhotos();
            }
            // Очищаем форму
            resetPopupForm($popup);
            $popup.removeClass('is-open');
            $popup.removeClass("is-ok");
            $("body").removeClass("is-hidden");
        }
    });

    function resetPopupForm(popup) {
        resetAllTimers();
        zapisPhoneVerification.resetCountdown();

        const $form = popup.find('form');
        let fullResetFormIDS = ['autor-form-password','autorization-form'];
        let inputsToClear;
        if (window.user && !fullResetFormIDS.includes($form.attr('id'))) {
            // Для авторизованных: исключаем name, phone, скрытые поля и чекбоксы
            inputsToClear = $form.find("input:not([type='radio'], [type='checkbox'], [type='hidden'], [name='phone'], [name='name'], [name='email'])")
                .not("[aria-hidden='true']")
                .not("[name^='my_name']")
                .not("[name='valid_from']")
                .filter(function() {
                    return $(this).css("display") !== "none";
                });

            // Подменяем значения для полей name, phone и email
            let nameInput = $form.find("input[name='name']");
            let phoneInput = $form.find("input[name='phone']");
            let emailInput = $form.find("input[name='email']");

            if (nameInput.length && window.user.name) {
                nameInput.val(window.user.name);
            }
            if (phoneInput.length && window.user.phone) {
                phoneInput.val(window.user.phone);
            }
            if (emailInput.length && window.user.email) {
                emailInput.val(window.user.email);
            }
        } else {
            inputsToClear = $form.find("input:not([type='checkbox'], [type='hidden'])")
                .not("[aria-hidden='true']")
                .not("[name^='my_name']")
                .not("[name='valid_from']")
                .not(".not__clear-phone input[name='phone']")
                .filter(function() {
                    return $(this).css("display") !== "none";
                });
        }

        if ($("#reviews-form").length > 0) {
            let form = $("#reviews-form");
            form.find('input[type="checkbox"]').prop('checked', false).parents(".js-form-field").removeClass("is-error is-filled");
            form.find("textarea[name='description']").val('').parents(".js-form-field").removeClass("is-filled");
            console.log(filesArray);
            filesArray = [];

            // Очищаем все превью
            $('.preview-box').empty();

            // Сброс значения у всех инпутов
            $('input[type="file"][name="photos[]"]').val('');
        }

        if ($("#cancel-form").length > 0) {
            let form = $("#cancel-form");
            form.find('input[type="checkbox"]').prop('checked', false).parents(".js-form-field").removeClass("is-error is-filled");
            form.find("textarea[name='reason-input'], textarea[name='description-cancel']").val('').parents(".js-form-field").removeClass("is-filled");
            form.find('.cancel-step-js').removeClass('cancel-step__active');
            form.find('.cancel-step-js[data-step="1"]').addClass('cancel-step__active');
        }


        // Сброс чекбоксов
        $form.find('input[type="checkbox"]').prop('checked', false);
        $form.find('input[type="radio"]').prop('checked', false);

        // Удаление классов ошибок и стилей
        // $form.find('.js-form-field').removeClass('is-error is-filled');
        inputsToClear.val('').blur().parents(".js-form-field").removeClass("is-error is-filled");

        // Перерисовка кастомных селектов
        $form.find('select').styler('destroy').styler();

        // Сброс табов
        const $tabNav = popup.find('.autorization__tab-nav');
        const $tabs = $tabNav.find('[data-tab]');
        $tabs.removeClass('is-active').first().addClass('is-active');

        const $tabContent = popup.find('.autorization__tab-box');
        const activeTabId = $tabs.first().data('tab') + '-cnt';
        $tabContent.find('.autorization__tab-cnt')
            .removeClass('is-active')
            .filter(`#${activeTabId}`)
            .addClass('is-active');

        // Сброс шагов (data-step)
        const $steps = popup.find('[data-step]');
        $steps.removeClass('is-active');
        if ($steps.length > 0) {
            $steps.first().addClass('is-active');
        }

        if (popup.data('popup') == 'zapis'){
            $('.form-hide').show();
            $('.form-hide').removeClass('not__clear-phone');
            $('.zapis__pin').hide();
            $('.zapis__pin').removeClass('is-active');
        }

        if (popup.data('popup') == 'autorization'){
            $(".popup__name-autorization").text('Авторизация')
        }
    }

    function clearAllPhotos() {
        filesArray = []; // Очищаем массив файлов
        $('#preview').empty(); // Удаляем все миниатюры с экрана
        // updateInputFiles(); // Очищаем input
    }

    // табы авторизации
    $(".autorization__tab-item").on("click", function (e) {
        e.preventDefault();

        var tabId = $(this).data("tab");

        $(".autorization__tab-cnt").removeClass("is-active");

        $("#" + tabId + "-cnt").addClass("is-active");

        $(".autorization__tab-item").removeClass("is-active");
        $(this).addClass("is-active");
        if (tabId === 'password') {
            $(".popup__name-autorization").text('Авторизация')
        } else if ($('.autorization-step[data-step="2"]').hasClass('is-active')) {
            $(".popup__name-autorization").text('Код подтверждения')
        }
    });

    /*авторизация*/
    $('.next-autorization-step').on('click', function (event) {
        event.preventDefault();
        let form = $(this).closest('form')[0];
        let formData = new FormData(form);

        const phoneInput = $('#autorization-form input[name="phone"]');
        const phoneValue = phoneInput.val().trim();
        const privacyCheck = $('#autorization-form .aggree-check');

        if (phoneValue === '') {
            phoneInput.parent().find('.form__error span').text('Поле "Телефон" обязательно для заполнения.');
            phoneInput.parent().addClass('is-error');
        } else {
            phoneInput.parent().removeClass('is-error');
        }

        //!!!!
        //если пользователя с таким номером не нашли то phoneInput.parent().find('.form__error span').text('Пользователь с таким номером не найден');

        if (!privacyCheck.is(':checked')) {
            privacyCheck.parent().addClass('is-error');
            privacyCheck.closest('.popup__info').addClass('popup__info-error');
        } else {
            privacyCheck.parent().removeClass('is-error');
            privacyCheck.closest('.popup__info').removeClass('popup__info-error');
        }

        if (phoneValue !== '' && privacyCheck.is(':checked')) {

            $.ajax({
                url: "/auth/login-sms",
                method: 'post',
                processData: false,
                contentType: false,
                data: formData,
                headers: {
                    'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
                }
            }).done(function (response) {

                $('.autorization-step[data-step="1"]').removeClass('is-active');
                // $('.autorization-step[data-step="1"]').addClass('not__clear-phone');
                $('.autorization-step[data-step="2"]').addClass('is-active');

                $(".popup__name-autorization").text('Код подтверждения');

                // Маскируем и выводим номер телефона на втором шаге
                const maskedPhone = maskPhoneNumber(phoneValue); // номер для примера
                $('#autorization-form .popup__text-custom span').text(maskedPhone);

                startTimer(60, $('.autorization-step[data-step="2"] .counter__block span'), $('.js-resend-btn'));

            }).fail(function (response) {
                phoneInput.parent().find('.form__error').addClass('is-activity');
                phoneInput.parent().find('.form__error span').html(response.responseJSON.message);
                phoneInput.parent().addClass('is-error');
            });

        }
    });

    $('.js-submit-signing').on('click', function (e) {
        e.preventDefault()
        let form = $(this).closest('form')[0];
        let formData = new FormData(form);

        $.ajax({
            url: "/auth/confirm-code",
            method: 'post',
            processData: false,
            contentType: false,
            data: formData,
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
            }
        }).done(function (response) {
            if (response.redirect_url) {
                window.location.href = response.redirect_url;
            }

        }).fail(function (response) {
            console.error('Ошибка при запросе:', response);

            let errorMessage = 'Неизвестная ошибка. Попробуйте позже.';

            if (response.responseJSON && response.responseJSON.message) {
                errorMessage = response.responseJSON.message.replace("verification code", "Код подтверждения");
            } else if (response.responseText) {
                errorMessage = response.responseText;
            }

            // Выводим сообщение об ошибке на форму
            $('.pin__block-box').addClass('is-error');
            $('.pin__block-box .form__error span').text(errorMessage);
        });

    })

    $('.js-submit-signing-password').submit(function (e) {
        e.preventDefault()
        let form = $(this).closest('form')[0];
        let formData = new FormData(form);
        let $form = $(this);
        let $submitButton = $form.find('button[type="submit"]');
        formData.set('login', formData.get('phone'));

        const privacyCheck = $(this).closest('form').find('.aggree-check');

        if (!privacyCheck.is(':checked')) {
            privacyCheck.parent().addClass('is-error');
            privacyCheck.closest('.popup__info').addClass('popup__info-error');
        } else {
            privacyCheck.parent().removeClass('is-error');
            privacyCheck.closest('.popup__info').removeClass('popup__info-error');
        }

        // Проверка флага, чтобы убедиться, что форма не отправляется повторно
        if ($form.data('isSubmitting')) return;

        // Устанавливаем флаг, что форма отправляется
        $form.data('isSubmitting', true);

        // Отключаем кнопку submit, чтобы предотвратить повторные нажатия
        $submitButton.prop('disabled', true);
        $('.js-form-field').removeClass('is-error');


        $.ajax({
            url: "/auth/login",
            method: 'post',
            processData: false,
            contentType: false,
            data: formData,
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
            }
        }).done(function (response) {
            $form.data('isSubmitting', false); // Сбрасываем флаг отправки
            $submitButton.prop('disabled', false);
            if (response.redirect_url) {
                window.location.href = response.redirect_url;
            }

        }).fail(function (response) {
            $form.data('isSubmitting', false); // Сбрасываем флаг отправки
            $submitButton.prop('disabled', false);

            // if (response.status == "401") {
            //     $form.find('[name="phone"]')
            //         .parents(".js-form-field")
            //         .addClass('is-error')
            //         .find(".form__error span")
            //         .html("Пользователь с таким логином и паролем не найден")
            // }

            if (response.status == "401") {
                $form.find('.not__login')
                    .addClass('is-error')
                    .find("span")
                    .html("Пользователь с таким логином и паролем не найден")
            }

            $form.find('input').on('input keydown change', function () {
                $form.find('.not__login').removeClass('is-error').find("span").html('');
            });

            $.each(response.responseJSON.errors, function (field_name, error) {
                field_name = field_name === 'login'? 'phone' : field_name

                $form.find('[name=' + field_name + ']')
                    .parents(".js-form-field")
                    .addClass('is-error')
                    .find(".form__error span")
                    .html(error)

            })
        });

    })


    /*регистрация*/
    $('.next-reg-step').on('click', function (e) {
        e.preventDefault();
        let form = $(this).closest('form')[0];
        let formData = new FormData(form);

        const phoneInput = $('#reg-form input[name="phone"]');
        const phoneValue = phoneInput.val().trim();
        const privacyCheck = $('#reg-form .aggree-check');

        if (phoneValue === '') {
            phoneInput.parent().find('.form__error span').text('Поле "Телефон" обязательно для заполнения.');
            phoneInput.parent().addClass('is-error');
        } else {
            phoneInput.parent().removeClass('is-error');
        }

        if (!privacyCheck.is(':checked')) {
            privacyCheck.parent().addClass('is-error');
            privacyCheck.closest('.popup__info').addClass('popup__info-error');
        } else {
            privacyCheck.parent().removeClass('is-error');
            privacyCheck.closest('.popup__info').removeClass('popup__info-error');
        }

        // Добавляем значение телефона в formData
        formData.set('phone', phoneValue);


        // Получаем значения паролей
        const password = formData.get('password');
        const confirmPassword = formData.get('password_confirmation');

        if (!password.length > 0){
            $(form).find('[name="password"]')
                .parents(".js-form-field")
                .addClass('is-error')
                .find(".form__error span")
                .text("Пароль и подтверждение пароля обязательны.");
        }
        if (!confirmPassword.length > 0){
            $(form).find('[name="password_confirmation"]')
                .parents(".js-form-field")
                .addClass('is-error')
                .find(".form__error span")
                .text("Пароль и подтверждение пароля обязательны.");
        }
        // Проверяем, что пароли совпадают
        if (password !== confirmPassword) {
            $(form).find('[name="password_confirmation"]')
                .parents(".js-form-field")
                .addClass('is-error')
                .find(".form__error span")
                .text("Пароли не совпадают.");
            return;
        }

        if (phoneValue === '' || !privacyCheck.is(':checked')) {
            return;
        }

        if (password.length < 6) {
            $(form).find('[name="password"]')
                .parents(".js-form-field")
                .addClass('is-error')
                .find(".form__error span")
                .text("Пароль должен быть больше 6 символов")
            return;
        }

        // Отправка AJAX-запроса
        $.ajax({
            url: "/auth/register",
            method: 'post',
            data: formData,
            processData: false, // Важно
            contentType: false, // Важно
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
            }
        }).done(function (response) {
            $('.reg-step[data-step="1"]').removeClass('is-active');
            $('.reg-step[data-step="2"]').addClass('is-active');
            // Маскируем и выводим номер телефона на втором шаге
            $('#reg-form .popup__text-custom span').text(maskPhoneNumber(phoneValue));

            startTimer(60, $('.reg-step[data-step="2"] .counter__block span'), $('.js-resend-btn'));

        }).fail(function (response) {
            $.each(response.responseJSON.errors, function (field_name, error) {

                $(form).find('[name=' + field_name + ']')
                    .parents(".js-form-field")
                    .addClass('is-error')
                    .find(".form__error span")
                    .text(error)
            })
        });
    });

    $('#reg-form .aggree-check, #autorization-form .aggree-check, #autor-form-password .aggree-check').on('change', function () {
        if ($(this).is(':checked')) {
            $(this).parent().removeClass('is-error');
            $(this).closest('.popup__info').removeClass('popup__info-error');
        }
    });

    // Пин-код

    $(".pin__block").each(function () {
        const $pinContainer = $(this);
        const $hiddenInput = $("<input type='hidden' class='verificationCode' name='verification_code' />");

        // Добавляем скрытое поле в форму
        $pinContainer.closest("form").append($hiddenInput);

        // Функция для обновления скрытого поля
        const updateHiddenInput = () => {
            const pinCode = $pinContainer.find("input").map((_, el) => $(el).val()).get().join('');
            $hiddenInput.val(pinCode);
        };

        // Обработка событий на input
        $pinContainer.on("keydown", "input", function (e) {
            const $input = $(this);

            // Перемещение по полям ввода
            if (e.key === "Backspace" && !$input.val()) {
                $input.prev("input").focus();
                e.preventDefault();
            } else if (e.key === "ArrowLeft") {
                $input.prev("input").focus();
                e.preventDefault();
            } else if (e.key === "ArrowRight") {
                $input.next("input").focus();
                e.preventDefault();
            } else if (!/[0-9]/.test(e.key) && !["Backspace", "ArrowLeft", "ArrowRight"].includes(e.key)) {
                // Разрешаем вставку через Ctrl+V или Shift+Insert
                if ((e.ctrlKey || e.metaKey) && e.key === 'v' || (e.shiftKey && e.key === 'Insert')){}
                else {
                    e.preventDefault(); // Блокируем все, кроме допустимых клавиш
                }

            }
            $('.pin__block-box').removeClass('is-error');
        });

        // Обработка ввода
        $pinContainer.on("input", "input", function () {
            const $input = $(this);

            // Ограничиваем длину через JS
            if ($input.val().length > 1) {
                $input.val($input.val().slice(0, 1));
            }
            if ($input.val()) {
                $input.next("input").focus();
            }
            updateHiddenInput();
            $('.pin__block-box').removeClass('is-error');
        });

        // Обработка вставки из буфера обмена
        $pinContainer.on("paste", "input", function (e) {
            // Отключаем стандартное поведение вставки
            e.preventDefault();

            let clipboardData;

            // Для современных браузеров
            if (e.originalEvent && e.originalEvent.clipboardData) {
                clipboardData = e.originalEvent.clipboardData.getData("text");
            }
            // Для старых браузеров (например, Internet Explorer)
            else if (window.clipboardData) {
                clipboardData = window.clipboardData.getData("Text");
            }
            // Если clipboardData все равно не удалось получить
            if (!clipboardData) {
                console.error("Clipboard data is not available.");
                return;
            }

            // Оставляем только цифры
            const pasteData = clipboardData.replace(/\D/g, '');
            const $inputs = $pinContainer.find("input");

            // Заполняем поля ввода
            pasteData.split('').forEach((char, index) => {
                if (index < $inputs.length) {
                    $inputs.eq(index).val(char);
                }
            });

            // Ставим фокус на последнее заполненное поле
            const lastFilledIndex = Math.min(pasteData.length, $inputs.length) - 1;
            if ($inputs.eq(lastFilledIndex).length) {
                $inputs.eq(lastFilledIndex).focus();
            }

            // Обновляем скрытое поле с пин-кодом
            updateHiddenInput();
            $('.pin__block-box').removeClass('is-error');
        });
    });

    $('#autorization-form .js-resend-btn, #reg-form .js-resend-btn').click(function (e) {
        e.preventDefault();
        let form = $(this).closest('form')[0];

        if (form.id !== 'autorization-form' && form.id !== 'reg-form') {
            return; // Если форма не соответствует, выйти
        }

        let formData = new FormData(form);
        let resendBtn =  $(this);
        let displayCounter = $(this).parent().find("span");

        $.ajax({
            url: "/auth/resend-code",
            method: 'post',
            data: formData,
            processData: false, // Важно
            contentType: false, // Важно
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
            }
        }).done(function (response) {
            // resendBtn.hide()
            startTimer(60,  displayCounter, resendBtn);
        }).fail(function (response) {
            console.error(response)
        });

    })

    // таймер
    function startTimer(duration, display,resendBtn) {
        if (display.data('timer-id')) clearInterval(display.data('timer-id'));
        let timer = duration;

        let timerId = setInterval(function () {
            display.text(timer);
            display.data('timer-id', timerId);

            if (--timer < 0) {
                clearInterval(timerId);
                display.text("0");
                resendBtn.show();

            }
        }, 1000);
    }

    function resetAllTimers() {
        // Сброс UI элементов
        $('.counter__block span').text('60');
        $('.js-resend-btn').show().prop('disabled', false);
        $('.count-inline').removeClass('hide-text');

        $('[data-timer-id]').each(function(i) {
            let timerId = $(this).data('timer-id');
            clearInterval(timerId);
            $(this).removeData('timer-id');
        });

    }

    //маскировка номера телефона
    function maskPhoneNumber(phone) {
        return phone.replace(/(\+7 \(\d{3}\))\d{3}(\d{2})(\d{2})/, '$1xxx$2$3');
    }

        // Элементы формы
        const $passwordInput = $('.js-password');
        const $passwordStrength = $('.js-password-strength');
        const $passwordConfirmationInput = $('.js-password_confirmation');
        const $passwordMatch = $('.js-password-match');

        /**
         * Проверка сложности пароля
         * @param {string} password - Введенный пароль
         * @returns {{level: string, className: string}} - Текст сложности (слабый, средний, сильный)
         */
        function getPasswordStrength(password) {
            if (password.length < 6) {
                return { level: 'Слабый', className: 'strength-weak', title: 'Пароль слишком короткий!' };
            }
            const hasLower = /[a-z]/.test(password);
            const hasUpper = /[A-Z]/.test(password);
            const hasDigit = /[0-9]/.test(password);
            const hasSpecial = /[^a-zA-Z0-9]/.test(password);

            if (hasLower && hasUpper && hasDigit && hasSpecial) {
                return { level: 'Сильный', className: 'strength-strong', title: 'Пароль надежный' };
            }
            if (hasLower && hasUpper && hasDigit) {
                return { level: 'Средний', className: 'strength-medium', title: 'Добавьте символы для усиления' };
            }
            return { level: 'Слабый', className: 'strength-weak', title: 'Пароль слишком простой' };
        }

        /**
         * Обновление отображения сложности пароля
         */
        function updatePasswordStrength() {
            const password = $passwordInput.val();
            const { level, className, title } = getPasswordStrength(password);

            $passwordStrength
                .removeClass('strength-weak strength-medium strength-strong')
                .addClass(className)
                // .text(level);
                .attr('title', title);

        }

        /**
         * Проверка совпадения паролей
         */
        function updatePasswordMatch() {
            const password = $passwordInput.val();
            const confirmation = $passwordConfirmationInput.val();
            const isMatch = password === confirmation;

            $passwordMatch
                .removeClass('match-success match-fail')
                .addClass(isMatch ? 'match-success' : 'match-fail')
                // .text(isMatch ? '' : 'Пароли не совпадают');
                .attr('title', isMatch ? '' : 'Пароли не совпадают');

        }

        // События ввода
        $passwordInput.on('input', updatePasswordStrength);
        $passwordConfirmationInput.on('input', updatePasswordMatch);

        // Обновление состояния при загрузке (на случай предзаполненных форм)
        // updatePasswordStrength();
        // updatePasswordMatch();

        /*выбор регионов*/
        /*закрытие попапа с уточнением вашего региона */
        $('.confirmation__popup .popup__close-btn, .confirmation__popup .confirm-yes').on('click', function() {
            $('.confirmation__popup-box').removeClass('is-open');
            $('body').removeClass('is-hidden');
        });

        /*открытие попапа с выбором регионов при клике на изменить*/
        $('.popup__choice .confirm-change').on('click', function() {
            $('.confirmation__popup-box').removeClass('is-open');
            $('.regions__popup-box').addClass('is-open');
        });

        /*закрытие попапа с выбором региона региона*/
        $('.regions__popup .popup__close-btn').on('click', function() {
            $('.regions__popup-box').removeClass('is-open');
            $('body').removeClass('is-hidden');
        });

        let popupKey = 'popupShown';
        let regionKey = 'selectedRegion';
        let popupLifetime = 30 * 24 * 60 * 60 * 1000; // 30 дней

        let lastShown = localStorage.getItem(popupKey);
        let savedRegion = localStorage.getItem(regionKey);
        // let currentRegion = $('.confirmation__popup .popup__text').text().trim(); // Берем регион из попапа
        let currentRegion = window.currentRegion?.name;

        console.log('Текущий регион:', currentRegion);
        console.log('Сохраненный регион в кеше:', savedRegion);

        // Проверяем, показывать ли попап
        if (!savedRegion || savedRegion !== currentRegion) {
            $('.confirmation__popup-box').addClass('is-open');

            // Сохраняем регион в localStorage
            localStorage.setItem(regionKey, currentRegion);
            localStorage.setItem(popupKey, Date.now());
        } else if (lastShown && (Date.now() - lastShown > popupLifetime)) {
            // Если 30 дней прошло, сбрасываем кеш и снова проверяем регион
            localStorage.removeItem(regionKey);
            localStorage.removeItem(popupKey);
        }

        $('.js-change-region').click(function (e){
           e.preventDefault();
           let id = $(this).data('id');
           let name = $(this).text().trim();
            $.ajax({
                url: '/regions/set',
                method: 'post',
                data: {
                    region_id: id
                },
                success: function (response) {
                    console.log('Выбран новый регион:', response.region.name);
                    $('.confirmation__popup-box .popup__text').text(response.region.name);
                    $('div.city__item > span').text(response.region.name);
                    $('.js-change-region').removeClass('is-active');
                    $('.js-change-region[data-id="' + id + '"]').addClass('is-active');

                    localStorage.setItem(regionKey, response.region.name);
                    localStorage.setItem(popupKey, Date.now());

                    location.reload();
                }
            });
        });

        $("#password, #password_confirmation").on("input", function () {
            $(this).val($(this).val().replace(/\s+/g, ""));
        });

        function initScrollableFilter(selector) {
            let isDown = false;
            let startX;
            let scrollLeft;
            const $filter = $(selector);

            // Прокрутка колесом мыши
            $filter.on("wheel", function (event) {
                event.preventDefault();
                let scrollAmount = event.originalEvent.deltaY;
                $(this).stop().animate({ scrollLeft: "+=" + scrollAmount }, 200, "swing");
            });

            // Перетаскивание мышью (drag-scroll)
            $filter.on("mousedown", function (event) {
                isDown = true;
                startX = event.pageX - $filter.offset().left;
                scrollLeft = $filter.scrollLeft();
                $filter.addClass("active"); // Визуальная индикация
            });

            $(document).on("mouseup", function () {
                isDown = false;
                $filter.removeClass("active");
            });

            $(document).on("mousemove", function (event) {
                if (!isDown) return;
                event.preventDefault();
                const x = event.pageX - $filter.offset().left;
                const walk = (x - startX) * 1.5; // Коэффициент для скорости движения
                $filter.scrollLeft(scrollLeft - walk);
            });

            // Прокрутка при клике
            $filter.on("click", ".services__filter-item", function () {
                let itemLeft = $(this).position().left;
                let itemWidth = $(this).outerWidth();
                let containerScrollLeft = $filter.scrollLeft();
                let containerWidth = $filter.width();

                let scrollTo = containerScrollLeft + itemLeft - containerWidth / 2 + itemWidth / 2;

                // Проверяем, выходит ли элемент за левый край
                if (itemLeft < 0) {
                    scrollTo = containerScrollLeft + itemLeft;
                }
                // Проверяем, выходит ли элемент за правый край
                else if (itemLeft + itemWidth > containerWidth) {
                    scrollTo = containerScrollLeft + itemLeft - containerWidth + itemWidth;
                }

                $filter.stop().animate({ scrollLeft: scrollTo }, 300, "swing");
            });
        }

        initScrollableFilter("#services__filter");

        let filterInitialized = false;

        function checkScreenWidthAndInit() {
            if ($(window).width() <= 600 && !filterInitialized) {
            initScrollableFilter(".applications__serv-block");
            filterInitialized = true;
            }
        }
        checkScreenWidthAndInit();

        $(window).on('resize', function() {
            checkScreenWidthAndInit();
        });

});





//# sourceMappingURL=main.js.map
