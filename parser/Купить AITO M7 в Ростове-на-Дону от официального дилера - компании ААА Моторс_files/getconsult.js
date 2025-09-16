$(document).ready(function () {
    let headerHeight = $("header").height()
    $(".consult__form").validate({
        focusCleanup: true,
        focusInvalid: false,
        rules: {
            name: {
                required: true,
                maxlength: 100
            },
            phone:{
                required: true,
            },
            privacy:{
                required: true
            }
        },
        messages: {
            name: {
                required: 'Поле "Имя" обязательно к заполнению',
                maxlength: jQuery.validator.format("Не должно превышать {0} символов")
            },
            phone: {
                required: 'Поле "Телефон" обязательно к заполнению',
                maxlength: jQuery.validator.format("Не должно превышать {0} символов")
            },
            privacy: "Нужно согласиться с условиями использования и обработкой персональных данных."
        },
        errorPlacement: function(error, element) {
            // element.parent().addClass('is-error')
            element.parent().find("span").text(error.text());
        },
        highlight: function(element) {
            if ($(element).attr("name") === "privacy") {
                $(element).closest('.js-form-field').addClass('is-error');
            } else {
                $(element).closest('.form__field').addClass('is-error');
                $('html, body').animate({
                    scrollTop: $(".consult__form").offset().top - headerHeight
                }, 500);
            }
        },
        unhighlight: function(element) {
            if ($(element).attr("name") === "privacy") {
                $(element).closest('.js-form-field').removeClass('is-error');
            } else {
                $(element).closest('.form__field').removeClass('is-error');
            }
        },
        submitHandler:function(form, e) {
            consultFormSubmit(e)
        },
    })

    function consultFormSubmit (e) {

        $(e.target).find($('.is-error')).each(function() {
            $( this ).removeClass( "is-error" );
        })

        e.preventDefault();
        let page = $(location).attr('href');

        var info = 'false';
        if($('.consult__form input[name="info"]').prop('checked')){info='true'}

        let formData = new FormData();

        // Перезаписываем данные с помощью .set
        formData.set('name', $('.consult__form input[name="name"]').val());
        formData.set('phone', $('.consult__form input[name="phone"]').val());
        formData.set('privacy', $('.consult__form input[name="privacy"]').prop('checked'));
        formData.set('info', info);
        formData.set('description-question', "-");


        e.preventDefault(), $(".postme").val("Секунду, идет отправка"), $.ajaxSetup({
            headers: {
                "X-CSRF-TOKEN": $('meta[name="csrf-token"]').attr("content")
            }
        }), $.ajax({
            enctype: 'multipart/form-data',
            type: "post",
            url: "/api/consult",
            data: formData,
            processData: false,  // Important!
            contentType: false,
            cache: false,
            success: function (res) {

                $('.consult-popup-ok.popup').addClass("is-open is-ok")
                $('.consult__form input[name="name"]').val('')
                $('.consult__form input[name="phone"]').val('')
                $('.consult__form input[name="info"]').prop("checked",false);

                setTimeout(function () {
                    $(".consult-popup-ok.popup").removeClass("is-open is-ok");
                }, 2500);
            },
            error: function () {
            }
        })
    }

})
