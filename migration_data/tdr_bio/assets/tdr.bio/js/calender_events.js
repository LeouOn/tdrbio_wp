jQuery(document).ready(function() {
    jQuery('.calendar').prepend('<img id="loading-image" src="' + calenderEvents.homeurl + '/images/loader.gif" alt="Loading..." />');
      jQuery('.calendar').fullCalendar({
        monthNames: calenderEvents.monthNames,
        monthNamesShort: calenderEvents.monthNamesShort,
        dayNames: calenderEvents.dayNames,
        dayNamesShort: calenderEvents.dayNamesShort,
        editable: true,
		eventLimit: 3,
		viewRender: function (view, element) {
		var b = jQuery('.calendar').fullCalendar('getDate');
		this_month = b.format('YYYY-MM-01');
		jQuery('.calendar').fullCalendar('removeEventSource', calenderEvents.homeurl + '/includes/json-feed.php'); 
		jQuery('.calendar').fullCalendar('refetchEvents');
		jQuery('.calendar').fullCalendar('addEventSource', { url: calenderEvents.homeurl + '/includes/json-feed.php',
						type: 'POST',
						data: {
						   event_cat_id: jQuery('.event_calendar').attr('id'),
						   month_event: this_month,
						  }})
		jQuery('.calendar').fullCalendar('refetchEvents');
	 	},
		googleCalendarApiKey: calenderEvents.googlekey,
			eventSources: [
				{
					googleCalendarId:calenderEvents.googlecalid
					
				},
				],
        timeFormat: calenderEvents.time_format,
        firstDay:calenderEvents.start_of_week,
        loading: function(bool) {
            if (bool)
                jQuery('#loading-image').show();
            else
                jQuery('#loading-image').hide();
        },
    });
});