def fetch_leads_from_indiamart():
    log("Starting fetch_leads_from_indiamart function", level='info')

    API_KEY = 'mRywErBl43jGSPev5neI7lqGoVTGlDI='

    # Get current UTC time
    end_time_utc = datetime.datetime.utcnow()

    # Calculate start time (5 minutes before end time)
    start_time_utc = end_time_utc - datetime.timedelta(minutes=5)

    # Add 5 hours 30 minutes to convert UTC to IST
    ist_time_difference = datetime.timedelta(hours=5, minutes=30)

    # Convert start and end times to IST by adding the time difference
    start_time_ist = start_time_utc + ist_time_difference
    end_time_ist = end_time_utc + ist_time_difference

    # Format the times in 'dd-Mon-yyyy HH:MM:SS' format
    start_time_str = start_time_ist.strftime('%d-%b-%Y %H:%M:%S')
    end_time_str = end_time_ist.strftime('%d-%b-%Y %H:%M:%S')

    # Build the API URL
    api_url = f"https://mapi.indiamart.com/wservce/crm/crmListing/v2/?glusr_crm_key={API_KEY}&start_time={start_time_str}&end_time={end_time_str}"
    
    try:
        log("Sending GET request to IndiaMart API", level='info')
        response = requests.get(api_url)
        data = response.json()

        log(f"Data: {data}", level='info')  # Log the JSON data

        if data.get('CODE') == 200:
            log("Received successful response from IndiaMart API", level='info')

            created_leads = []
            
            for lead_data in data.get('RESPONSE', []):
                log(f"Lead Data: {lead_data}", level='info')

                crm_lead = {
                    'name': lead_data.get('SUBJECT') or 'Lead from IndiaMart',
                    'partner_name': lead_data.get('SENDER_NAME'),
                    'contact_name': lead_data.get('SENDER_NAME'),
                    'phone': lead_data.get('SENDER_MOBILE'),
                    'email_from': lead_data.get('SENDER_EMAIL'),
                    'description': lead_data.get('QUERY_MESSAGE'),
                    'street': lead_data.get('SENDER_ADDRESS'),
                    'city': lead_data.get('SENDER_CITY'),
                    'state_id': env['res.country.state'].search([('name', '=', lead_data.get('SENDER_STATE'))], limit=1).id,
                    'zip': lead_data.get('SENDER_PINCODE'),
                    'country_id': env['res.country'].search([('code', '=', lead_data.get('SENDER_COUNTRY_ISO'))], limit=1).id,
                    'type': 'lead',
                    'source_id': env['utm.source'].search([('name', '=', 'IndiaMart')], limit=1).id
                }
                
                lead = env['crm.lead'].create(crm_lead)
                created_leads.append(lead)
                # Create a notification with a link to the lead in the discussion
                message_body = f"New lead created: <a href='/web#id={lead.id}&model=crm.lead'>{lead.name}</a>"

                # Post the message to the lead's chatter
                lead.message_post(
                    body=message_body,
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',  # This will show as a comment-like notification
                )

            if record:
                record.unlink()

                log(f"Created Leads: {created_leads}", level='info')
        else:
            log(f"Failed to fetch new leads: IndiaMart API returned code {data.get('CODE')}. Message: {data.get('MESSAGE')}", level='warning')
            
    except Exception as e:
        log(f"Unexpected error occurred: {e}", level='error')

fetch_leads_from_indiamart()
