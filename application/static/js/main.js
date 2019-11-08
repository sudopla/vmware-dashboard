$(document).ready(function() {

    var $loading = $('.loader').hide();
    $(document)
        .ajaxStart(function () {
            $loading.show();
        })
        .ajaxStop(function () {
            $loading.hide();
        });

    //Event for menu
    $('.vms').click(function(){

        link = $(this).attr('data-link');
        name = $(this).text();
        $('#page_section').load(link, function(){
            $('.page-header1').html(name);
        });

    });
    $('.clusters').click(function(){

        link = $(this).parent('a').attr('data-link');
        name = $(this).text();
        $('#page_section').load(link, function(){
            $('.page-header1').html(name);
        });

    });
    $('.hosts').click(function(){

        link = $(this).attr('data-link');
        name = $(this).text();
        $('#page_section').load(link, function(){
            $('.page-header1').html(name);
        });

    });

    //Event for intervals
     $('#wrapper').on('click','button.btn',function(){

        link = $(this).attr('data-link');
        $('#graphs').load(link);
    });



});

