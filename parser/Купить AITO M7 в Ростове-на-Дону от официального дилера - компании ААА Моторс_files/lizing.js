$(document).ready(function () {

    $('.form__main').on('submit', function (e) {
        e.preventDefault();
        var error = false;

       if( !$('select[name="pay"]' ).val()){
           $('select[name="pay"]' ).parent().parent().parent().addClass('is-error')
           error = true
       }else {
           $('select[name="pay"]' ).parent().parent().parent().removeClass('is-error')
       }

        if( !$('select[name="term"]' ).val()){
            $('select[name="term"]' ).parent().parent().parent().addClass('is-error')
            error = true
        }else {
            $('select[name="term"]' ).parent().parent().parent().removeClass('is-error')
        }

        if( !$('input[name="name"]' ).val()){
            $('input[name="name"]').parent().addClass('is-error')
            error = true
        }else{
            $('input[name="name"]').parent().removeClass('is-error')
        }

        if( !$('input[name="phone"]' ).val()){
            $('input[name="phone"]').parent().addClass('is-error')
            error = true
        }else{
            $('input[name="phone"]').parent().removeClass('is-error')
        }

        if( !$('input[name="privacy"]' ).prop('checked')){
            $('input[name="privacy"]').parent().addClass('is-error')
            error = true
        }else{
            $('input[name="privacy"]').parent().removeClass('is-error')
        }



        if(!error){
           /* var sending = $('<p class="send_message">Отправляем данные на сервер</p>')*/
            /*sending.css("color", "green")*/
            /*$('.form__main').append(sending);*/

            var info = 'false';
            if($('.get_info').prop('checked')){info='true'}

            let formData = new FormData(e.target);

            // Перезаписываем или добавляем дополнительные данные в объект formData
            formData.set('type', 'lizing');  // Данные типа запроса
            formData.set('pay', $('select[name="pay"] option:selected').text());  // Селект для платежа
            formData.set('term', $('select[name="term"] option:selected').text());  // Селект для срока
            formData.set('name', $('input[name="name"]').val());  // Имя
            formData.set('phone', $('input[name="phone"]').val());  // Телефон
            formData.set('organization', $('input[name="organization"]').val());  // Организация
            formData.set('info', info);  // Информация о согласии
            formData.set('privacy', $('input[name="privacy"]').prop('checked'));  // Согласие на обработку данных
            formData.set('from_url', $(location).attr('href'));

                $.ajax({
                method: 'post',
                enctype: 'multipart/form-data',
                url: "/api/leasing",
                data: formData,
                processData: false,  // Important!
                contentType: false,
                cache: false,
                success: function (response) {
                    /*$('.form__main').addClass('is-ok')*/
                    $(".form__main .js-popup").addClass("is-open");
                    $(".form__main .js-popup").addClass("is-ok");
                    $("body").addClass("is-hidden");
                    setTimeout(function () {
                        $(".form__main .js-popup").removeClass("is-open");
                        $(".form__main .js-popup").removeClass("is-ok");
                        $("body").removeClass("is-hidden");
                    }, 3000);

                    /*$('.send_message').text('Данные успешно отправлены')*/
                    $('select[name="pay"]').val('')
                    $('select[name="pay"]').parent().find('.jq-selectbox__select-text').text( $('select[name="pay"]').attr( 'data-placeholder'))
                    $('select[name="term"]').val('')
                    $('select[name="term"]').parent().find('.jq-selectbox__select-text').text( $('select[name="term"]').attr( 'data-placeholder'))
                    $('input[name="name"]').val('')
                    $('input[name="phone"]').val('')
                    $('input[name="organization"]').val('')
                    $('.js-form-field').removeClass('is-filled');

                },
            })
        }

    });





})
