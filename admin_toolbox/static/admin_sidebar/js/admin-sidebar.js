(function ($) {

    $(document).on('click', '.su-sidebar-menu a.with-subitems', function(e) {
        e.preventDefault();
        var me = $(this);
        var li = me.closest('li');
        li.toggleClass('expanded');
    })

})(django.jQuery);