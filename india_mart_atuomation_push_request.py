log(f"New leads from IndiaMart: {payload}", level='info')
created_leads = []

if payload.get('CODE') == 200:
    # Access the main response in payload
    payload = payload.get('RESPONSE', {})
    try:
        # Retrieve state and country IDs
        state = env['res.country.state'].search([('name', '=', payload.get('SENDER_STATE'))], limit=1)
        country = env['res.country'].search([('code', '=', payload.get('SENDER_COUNTRY_ISO'))], limit=1)
        source = env['utm.source'].search([('name', '=', 'IndiaMart')], limit=1)
        
        crm_lead = {
            'name': payload.get('SUBJECT') or 'Lead from IndiaMart',
            'partner_name': payload.get('SENDER_NAME'),
            'contact_name': payload.get('SENDER_NAME'),
            'phone': payload.get('SENDER_MOBILE'),
            'email_from': payload.get('SENDER_EMAIL'),
            'description': payload.get('QUERY_MESSAGE'),
            'street': payload.get('SENDER_ADDRESS'),
            'city': payload.get('SENDER_CITY'),
            'state_id': state.id if state else False,
            'zip': payload.get('SENDER_PINCODE'),
            'country_id': country.id if country else False,
            'type': 'lead',
            'source_id': source.id if source else False
        }

        try:
            # Lead creation and committing to ensure data persistence
            lead = env['crm.lead'].create(crm_lead)
            created_leads.append(lead)
            env.cr.commit()  # Commit after lead creation
            log(f"Lead Created and Committed: {created_leads}", level='info')

            # Define message content for channel notification
            message_body = f"New lead created: <a href='/web#id={lead.id}&model=crm.lead' target='_blank'>{lead.name}</a>"

            # Find or create the notification channel for all users
            channel_name = "Lead Notifications"  # Define a clear name for your notification channel
            channel = env['mail.channel'].search([('name', '=', channel_name)], limit=1)

            if not channel:
                # If the channel doesn't exist, create it and add all users
                channel = env['mail.channel'].create({
                    'name': channel_name,
                    'channel_type': 'channel',  # Channel type for public notifications
                    'public': 'public',
                    'email_send': False,
                })

                # Add all active users to the channel
                all_users = env['res.users'].search([('active', '=', True)])
                channel.write({'channel_partner_ids': [(4, user.partner_id.id) for user in all_users]})
            
            # Post the notification message to the channel
            channel.message_post(
                body=message_body,
                subject="New Lead Notification",
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )
            log("Notification sent to all users via Discuss app channel", level='info')

        except Exception as e:
            log(f"Failed to create lead or post notification: {e}", level='error')

    except Exception as e:
        log(f"Failed to create lead: {e}", level='error')
else:
    log("Invalid CODE in payload", level='error')
