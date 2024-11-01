20X bot user guide:

Slash Commands:
	/create_event				//G3 MDT '680794825162883093'; Junior NCO '680795741417242804'; Senior NCO '680795766125887596'; Officer '680795785423880248'
	/add_recruit                //G1 RRT '680795063684694063'
	/goblin                     //Junior NCO '680795741417242804'; Senior NCO '680795766125887596'; Officer '680795785423880248'
	/add_service_record			//G1 PAT '701271883747950593'
	/get_service_record			//1 Platoon '680793435942289412'; Reserves '680794697387868170'
	/update_service_record      //G1 PAT '701271883747950593'

Command descriptions and params:
	/create_event
		Description: allows user to create an event.  Must be used in the channel where the event is to be posted.
			     RSVP will be created in specific RSVP channel(changeable by dev)
		Params:
		- event_name(required): The name that you want to give to the event (e.g. Operation Freedom)
		- event_description(required): short description of the event
		- event_date(required): The date of the event (DD/MM/YYYY)

	/add_recruit
		Description: gives the correct roles to a new recruit and sends welcome message into the welcome message channel(changeable by dev)
		Params:
		- user(required): discord name of the user (NOT NICKNAME OR GLOBAL NAME)
		- platoon(optional): platoon number to be placed in, MUST BE A NUMBER (e.g. 1)
		- section(optional): section number to be placed in, MUST BE A NUMBER (e.g. 2)
		- reserves(optional): yes or no (default: no) (if yes then platoon and section must be left empty)

	/goblin
		Description: try it ;)
		Params:
		- NONE

	/add_service_record
		Description: Creates a service record for a specified user
		Params:
		- user(required): discord name of the user (NOT NICKNAME OR GLOBAL NAME)
		- rank(required): Rank of the user 
			(e.g. Rifleman)
		- service_number(required): Users service number
		- zap_number(required): Users zap number
		- application_date(required): date user applied to the unit (DD/MM/YYYY)
		- qualifications(optional): qualifications of user with date, separated by commas 
			(e.g. FTCC(01/01/2001), BRU(10/10/2002), CIC(12/06/2003))
		- operations(optional): operations of user, separated by commas 
			(e.g. Operation Altis, Operation Stratis, Operation Malden)
		- staff_roles(optional): Staff roles of user and date appointed, separated by commas
			(e.g. RRT(01/01/2001), MDT(10/10/2002))
		- enlistment_history(optional): enlistment events and dates separated by comma
			(e.g. Accepted and appointed recruit(01/01/2001), Appointed Rifleman(10/10/2002))
		= assignment_history(optional): assignment events and dates, separated by commas
			(e.g. Assigned 5 Platoon, 1st ITB(01/01/2001), Assigned 2IC 1 Section(10/10/2002))

	/get_service_record
		Description: returns the service record of a specified user
		Params:
		- user(required): discord name of the user (NOT NICKNAME OR GLOBAL NAME)
	
	/update_service_record
		Description: adds entries to service record for a specified user
		Params:
		- user(required): discord name of the user (NOT NICKNAME OR GLOBAL NAME)
		- rank(optional): Rank of the user 
			(e.g. Rifleman)
		- service_number(optional): Users service number
		- zap_number(optional): Users zap number
		- application_date(optional): date user applied to the unit (DD/MM/YYYY)
		- qualifications(optional): qualifications of user, separated by commas 
			(e.g. FTCC(01/01/2001), BRU(10/10/2002), CIC(12/06/2003))
		- operations(optional): operations of user, separated by commas 
			(e.g. Operation Altis, Operation Stratis, Operation Malden)
		- staff_roles(optional): Staff roles of user and date appointed, separated by commas
			(e.g. RRT(01/01/2001), MDT(10/10/2002))
		- enlistment_history(optional): enlistment events and dates separated by comma
			(e.g. Accepted and appointed recruit(01/01/2001), Appointed Rifleman(10/10/2002))
		= assignment_history(optional): assignment events and dates, separated by commas
			(e.g. Assigned 5 Platoon, 1st ITB(01/01/2001), Assigned 2IC 1 Section(10/10/2002))
	
	/list_events
		Description: Lists all future events
		Params:
		- None
	
	/important_channels
		Description: Lists and links all important channels
		Params:
		- None