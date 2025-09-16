$(document).ready(function () {
    $('.form__file input[type=file]').on('change', function(){

        let file = this.files[0];

        $(this).closest('.form__file').find('.form__file-text').html(file.name ?? '');

    });

});
