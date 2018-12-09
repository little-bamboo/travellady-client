"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import datetime
import dateutil.parser
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


def generate_cruise_price(location, days, passengers, type):
    """
    Generates a number within a reasonable range that might be expected for a flight.
    The price is fixed for a given set of locations
    """
    cruise_types = ['Indoor', 'Cabin', 'Outside', 'Suite']
    cruise_price = 0
    for i in range(len(location)):
        cruise_price += ord(location.lower()[i])

    return passengers * (cruise_types.index(type) * cruise_price * days)


def generate_car_price(location, days, age, car_type):
    """
    Generates a number within a reasonable range that might be expected for a flight.
    The price is fixed for a given pair of locations.
    """

    car_types = ['economy', 'standard', 'midsize', 'full size', 'minivan', 'luxury']
    base_location_cost = 0
    for i in range(len(location)):
        base_location_cost += ord(location.lower()[i]) - 97

    age_multiplier = 1.10 if age < 25 else 1
    # Select economy is car_type is not found
    if car_type not in car_types:
        car_type = car_types[0]

    return days * ((100 + base_location_cost) + ((car_types.index(car_type) * 50) * age_multiplier))


def generate_hotel_price(location, nights, room_type):
    """
    Generates a number within a reasonable range that might be expected for a hotel.
    The price is fixed for a pair of location and roomType.
    """

    room_types = ['queen', 'king', 'deluxe']
    cost_of_living = 0
    for i in range(len(location)):
        cost_of_living += ord(location.lower()[i]) - 97

    return nights * (100 + cost_of_living + (100 + room_types.index(room_type.lower())))


def isvalid_cruise_type(cruise_type):
    cruise_types = ['Indoor', 'Cabin', 'Outside', 'Suite']
    return cruise_type.lower() in cruise_types


def isvalid_car_type(car_type):
    car_types = ['economy', 'standard', 'midsize', 'full size', 'minivan', 'luxury']
    return car_type.lower() in car_types


def isvalid_city(city):
    valid_cities = ['new york', 'los angeles', 'chicago', 'houston', 'philadelphia', 'phoenix', 'san antonio',
                    'san diego', 'dallas', 'san jose', 'austin', 'jacksonville', 'san francisco', 'indianapolis',
                    'columbus', 'fort worth', 'charlotte', 'detroit', 'el paso', 'seattle', 'denver', 'washington dc',
                    'memphis', 'boston', 'nashville', 'baltimore', 'portland']
    return city.lower() in valid_cities


def isvalid_room_type(room_type):
    room_types = ['queen', 'king', 'deluxe']
    return room_type.lower() in room_types


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def get_day_difference(later_date, earlier_date):
    later_datetime = dateutil.parser.parse(later_date).date()
    earlier_datetime = dateutil.parser.parse(earlier_date).date()
    return abs(later_datetime - earlier_datetime).days


def add_days(date, number_of_days):
    new_date = dateutil.parser.parse(date).date()
    new_date += datetime.timedelta(days=number_of_days)
    return new_date.strftime('%Y-%m-%d')


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_cruise(slots):
    print('Slots: \n')
    print(slots)

    departure_city = try_ex(lambda: slots['Location'])
    date_of_depature = try_ex(lambda: slots['Departure'])
    number_of_days = try_ex(lambda: slots['Days'])
    number_of_passengers = safe_int(try_ex(lambda: slots['Passengers']))
    cruise_type = try_ex(lambda: slots['CruiseType'])
    print(cruise_type)

    if not number_of_days:
        return build_validation_result(
            False,
            'Days',
            'How many days?'
        )

    if not number_of_passengers:
        return build_validation_result(
            False,
            'Passengers',
            'How many passengers?'
        )

    if not departure_city:
        return build_validation_result(
            False,
            'Location',
            'We current do not support {} as valid destination. Can you try a different city?'.format(departure_city)
        )

    if date_of_depature:
        if not isvalid_date(date_of_depature):
            return build_validation_result(
                False, 'Departure',
                'I did not understand your departure date.  What date would you like to go on your cruise?'.format(
                    date_of_depature)
            )

    print("Is valid cruise type: {0}.".format(isvalid_cruise_type(cruise_type)))

    if cruise_type and not isvalid_cruise_type(cruise_type):
        return build_validation_result(
            False,
            'CruiseType',
            'What cruise type did  you want?')

    return {'isValid': True}


def validate_car(slots):
    print("Slots: \n")
    print(slots)
    pickup_city = try_ex(lambda: slots['PickUpCity'])
    pickup_date = try_ex(lambda: slots['PickUpDate'])
    return_date = try_ex(lambda: slots['ReturnDate'])
    driver_age = safe_int(try_ex(lambda: slots['DriverAge']))
    car_type = try_ex(lambda: slots['CarType'])

    if pickup_city and not isvalid_city(pickup_city):
        return build_validation_result(
            False,
            'PickUpCity',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(pickup_city)
        )

    if pickup_date:
        if not isvalid_date(pickup_date):
            return build_validation_result(False, 'PickUpDate',
                                           'I did not understand your departure date. When would you like to pick up '
                                           'your car rental?')

        if dateutil.parser.parse(pickup_date) < datetime.datetime.today():
            return build_validation_result(False, 'PickUpDate',
                                           'Your pick up date is in the past!  Can you try a different date?')

    if return_date:
        if not isvalid_date(return_date):
            return build_validation_result(False, 'ReturnDate',
                                           'I did not understand your return date.  When would you like to return '
                                           'your car rental?')

    if pickup_date and return_date:
        if dateutil.parser.parse(pickup_date) >= dateutil.parser.parse(return_date):
            return build_validation_result(False, 'ReturnDate',
                                           'Your return date must be after your pick up date.  Can you try a different '
                                           'return date?')

        if get_day_difference(pickup_date, return_date) > 30:
            return build_validation_result(False, 'ReturnDate',
                                           'You can reserve a car for up to thirty days.  Can you try a different '
                                           'return date?')

    if driver_age is not None and driver_age < 18:
        return build_validation_result(
            False,
            'DriverAge',
            'Your driver must be at least eighteen to rent a car.  Can you provide the age of a different driver?'
        )

    if car_type and not isvalid_car_type(car_type):
        return build_validation_result(
            False,
            'CarType',
            'I did not recognize that model.  What type of car would you like to rent?  '
            'Popular cars are economy, midsize, or luxury')

    return {'isValid': True}


def validate_hotel(slots):
    location = try_ex(lambda: slots['Location'])
    checkin_date = try_ex(lambda: slots['CheckInDate'])
    nights = safe_int(try_ex(lambda: slots['Nights']))
    room_type = try_ex(lambda: slots['RoomType'])

    if location and not isvalid_city(location):
        return build_validation_result(
            False,
            'Location',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(location)
        )

    if checkin_date:
        if not isvalid_date(checkin_date):
            return build_validation_result(False, 'CheckInDate',
                                           'I did not understand your check in date.  When would you like to check in?')

        if dateutil.parser.parse(checkin_date) < datetime.datetime.today():
            return build_validation_result(False, 'CheckInDate',
                                           'Your check in date is in the past!  Can you try a different date?')

    if nights is not None and (nights < 1 or nights > 30):
        return build_validation_result(
            False,
            'Nights',
            'You can make a reservations for from one to thirty nights.  How many nights would you like to stay for?'
        )

    if room_type and not isvalid_room_type(room_type):
        return build_validation_result(False, 'RoomType',
                                       'I did not recognize that room type.  Would you like to stay in a queen, king,'
                                       ' or deluxe room?')

    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """


def book_hotel(intent_request):
    """
    Performs dialog management and fulfillment for booking a hotel.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    location = try_ex(lambda: intent_request['currentIntent']['slots']['Location'])
    checkin_date = try_ex(lambda: intent_request['currentIntent']['slots']['CheckInDate'])
    nights = safe_int(try_ex(lambda: intent_request['currentIntent']['slots']['Nights']))

    room_type = try_ex(lambda: intent_request['currentIntent']['slots']['RoomType'])
    session_attributes = intent_request['sessionAttributes']

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Hotel',
        'Location': location,
        'RoomType': room_type,
        'CheckInDate': checkin_date,
        'Nights': nights
    })

    session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_hotel(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price
        # back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.
        if location and checkin_date and nights and room_type:
            # The price of the hotel has yet to be confirmed.
            price = generate_hotel_price(location, nights, room_type)
            session_attributes['currentReservationPrice'] = price
        else:
            try_ex(lambda: session_attributes.pop('currentReservationPrice'))

        session_attributes['currentReservation'] = reservation
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # Booking the hotel.  In a real application, this would likely involve a call to a backend service.
    logger.debug('bookHotel under={}'.format(reservation))

    try_ex(lambda: session_attributes.pop('currentReservationPrice'))
    try_ex(lambda: session_attributes.pop('currentReservation'))
    session_attributes['lastConfirmedReservation'] = reservation

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation.   Please let me know if you would like to book a car '
                       'rental, or another hotel.'
        }
    )


def book_car(intent_request):
    """
    Performs dialog management and fulfillment for booking a car.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    slots = intent_request['currentIntent']['slots']
    pickup_city = slots['PickUpCity']
    pickup_date = slots['PickUpDate']
    return_date = slots['ReturnDate']
    driver_age = slots['DriverAge']
    car_type = slots['CarType']
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes = intent_request['sessionAttributes']
    last_confirmed_reservation = try_ex(lambda: session_attributes['lastConfirmedReservation'])
    if last_confirmed_reservation:
        last_confirmed_reservation = json.loads(last_confirmed_reservation)
    confirmation_context = try_ex(lambda: session_attributes['confirmationContext'])

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Car',
        'PickUpCity': pickup_city,
        'PickUpDate': pickup_date,
        'ReturnDate': return_date,
        'CarType': car_type
    })
    session_attributes['currentReservation'] = reservation

    if pickup_city and pickup_date and return_date and driver_age and car_type:
        # Generate the price of the car in case it is necessary for future steps.
        price = generate_car_price(pickup_city, get_day_difference(pickup_date, return_date), driver_age, car_type)
        session_attributes['currentReservationPrice'] = price

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_car(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Determine if the intent (and current slot settings) has been denied.  The messaging will be different
        # if the user is denying a reservation he initiated or an auto-populated suggestion.
        if confirmation_status == 'Denied':
            # Clear out auto-population flag for subsequent turns.
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            try_ex(lambda: session_attributes.pop('currentReservation'))
            if confirmation_context == 'AutoPopulate':
                return elicit_slot(
                    session_attributes,
                    intent_request['currentIntent']['name'],
                    {
                        'PickUpCity': None,
                        'PickUpDate': None,
                        'ReturnDate': None,
                        'DriverAge': None,
                        'CarType': None
                    },
                    'PickUpCity',
                    {
                        'contentType': 'PlainText',
                        'content': 'Where would you like to make your car reservation?'
                    }
                )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        if confirmation_status == 'None':
            # If we are currently auto-populating but have not gotten confirmation, keep requesting for confirmation.
            if (not pickup_city and not pickup_date and not return_date and not driver_age and not car_type) \
                    or confirmation_context == 'AutoPopulate':
                if last_confirmed_reservation and try_ex(
                        lambda: last_confirmed_reservation['ReservationType']) == 'Hotel':
                    # If the user's previous reservation was a hotel - prompt for a rental with
                    # auto-populated values to match this reservation.
                    session_attributes['confirmationContext'] = 'AutoPopulate'
                    return confirm_intent(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        {
                            'PickUpCity': last_confirmed_reservation['Location'],
                            'PickUpDate': last_confirmed_reservation['CheckInDate'],
                            'ReturnDate': add_days(
                                last_confirmed_reservation['CheckInDate'], last_confirmed_reservation['Nights']
                            ),
                            'CarType': None,
                            'DriverAge': None
                        },
                        {
                            'contentType': 'PlainText',
                            'content': 'Is this car rental for your {} night stay in {} on {}?'.format(
                                last_confirmed_reservation['Nights'],
                                last_confirmed_reservation['Location'],
                                last_confirmed_reservation['CheckInDate']
                            )
                        }
                    )

            # Otherwise, let native DM rules determine how to elicit for slots and/or drive confirmation.
            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        # If confirmation has occurred, continue filling any unfilled slot values or pass to fulfillment.
        if confirmation_status == 'Confirmed':
            # Remove confirmationContext from sessionAttributes so it does not confuse future requests
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            if confirmation_context == 'AutoPopulate':
                if not driver_age:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'DriverAge',
                        {
                            'contentType': 'PlainText',
                            'content': 'How old is the driver of this car rental?'
                        }
                    )
                elif not car_type:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'CarType',
                        {
                            'contentType': 'PlainText',
                            'content': 'What type of car would you like? Popular models are '
                                       'economy, midsize, and luxury.'
                        }
                    )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # Booking the car.  In a real application, this would likely involve a call to a backend service.
    logger.debug('bookCar at={}'.format(reservation))
    del session_attributes['currentReservationPrice']
    del session_attributes['currentReservation']
    session_attributes['lastConfirmedReservation'] = reservation
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation.'
        }
    )


def book_cruise(intent_request):
    """
    Performs dialog management and fulfillment for booking a cruise.

    Beyond fulfillment, the implementation for this intent demonstrats the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sesssionAttributes to pass information that can be used to guide conversation
    """

    slots = intent_request['currentIntent']['slots']
    departure_city = slots['Location']
    date_of_departure = slots['Departure']
    cruise_length = slots['Days']
    passenger_length = slots['Passengers']
    cruise_type = slots['CruiseType']

    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes = intent_request['sessionAttributes']
    last_confirmed_reservation = try_ex(lambda: session_attributes['lastConfirmedReservation'])

    if last_confirmed_reservation:
        last_confirmed_reservation = json.loads(last_confirmed_reservation)

    confirmation_context = try_ex(lambda: session_attributes['confirmationContext'])

    # Load confirmation history and track the current reservation
    reservation = json.dumps({
        'ReservationType': 'Cruise',
        'Location': departure_city,
        'Depature': date_of_departure,
        'Days': cruise_length,
        'Passengers': passenger_length,
        'CruiseType': cruise_type
    })

    print('booking cruise')
    print(reservation)

    session_attributes['currentReservation'] = reservation

    if departure_city and date_of_departure and passenger_length and cruise_length:
        # Build a new price and assign to the current session
        price = generate_cruise_price(departure_city, safe_int(cruise_length), safe_int(passenger_length), cruise_type)
        session_attributes['currentReservationPrice'] = price

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their values

        validation_result = validate_cruise(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Determine if the intent and current slot sessions has been denied.  The messaging will be different
        # if the user is denying a reservation he initiated or an auto-populated suggestion
        if confirmation_status == 'Denied':
            # Clear out auto-population
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            try_ex(lambda: session_attributes.pop('currentReservation'))
            if confirmation_context == 'AutoPopulate':
                return elicit_slot(
                    session_attributes,
                    intent_request['currentIntent']['name'],
                    {
                        'Location': None,
                        'Departure': None,
                        'Days': None,
                        'Passengers': None,
                        'CruiseType': None
                    },
                    'Location',
                    {
                        'contentType': 'PlainText',
                        'content': 'What departure city would you like for your cruise?'
                    }
                )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        if confirmation_status == 'None':
            # If we are currently autopopulating but have not gotten confirmation, keep requesting for confirmation.
            if (
                    not departure_city and not date_of_departure and not cruise_length and not passenger_length and
                    not cruise_type or confirmation_context == 'AutoPopulate'):
                if last_confirmed_reservation and try_ex(
                        lambda: last_confirmed_reservation['reservationType']) == 'Cruise':
                    session_attributes['confirmationContext'] = 'AutoPopulate'
                    return confirm_intent(
                        session_attributes,
                        intent_request,
                        intent_request['currentIntent']['name'],
                        {
                            'Location': last_confirmed_reservation['Location'],
                            'Departure': last_confirmed_reservation['Departure'],
                            'Days': last_confirmed_reservation['Days'],
                            'Passengers': last_confirmed_reservation['Passengers'],
                            'CruiseType': last_confirmed_reservation['CruiseType'],
                            'contentType': 'PlanText,',
                            'content': 'Is this the cruise from {0} on {1}'.format(
                                last_confirmed_reservation['Location'],
                                last_confirmed_reservation['Departure']
                            )
                        }
                    )

            # Otherwise let native DM rules determine how to eleicit for slots and/or ddrive
            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        # if conformation has occured continue filling any unfilled slot values or pass to fulfillment
        if confirmation_status == 'Confirmed':
            # Remove confirmationContext from sessionAttibutes so it does not confuse future request
            try_ex(lambda: session_attributes.pop('confirmationContent'))
            if confirmation_context:
                if not cruise_type:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'CruiseType',
                        {
                            'contentType': 'PlainText',
                            'content': 'What type cruise would you like to go on?  The choice is Indoor, Cabin, Outdoor, and Suite.'
                        }
                    )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'],
                                                   intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'BookHotel':
        return book_hotel(intent_request)
    elif intent_name == 'BookCar':
        return book_car(intent_request)
    elif intent_name == 'BookCruise':
        return book_cruise(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
