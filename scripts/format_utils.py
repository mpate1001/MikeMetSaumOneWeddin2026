"""
Utility functions for formatting phone numbers and validating addresses.
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Optional
import phonenumbers
import requests


def format_phone_number(phone: str, default_region: str = "US") -> str:
    """
    Format a phone number to a standard format.

    Args:
        phone: Raw phone number string
        default_region: Default region code (e.g., "US", "IN")

    Returns:
        Formatted phone number like "(XXX) XXX-XXXX" for US numbers,
        or international format for others.
        Returns original string if parsing fails.
    """
    if not phone or not phone.strip():
        return ""

    # Clean the input
    phone = phone.strip()

    try:
        # Try to parse the phone number
        parsed = phonenumbers.parse(phone, default_region)

        if not phonenumbers.is_valid_number(parsed):
            # Try without region assumption
            if phone.startswith('+'):
                parsed = phonenumbers.parse(phone)
            else:
                # Might be valid but just not matching region, return cleaned version
                digits = re.sub(r'\D', '', phone)
                if len(digits) == 10:
                    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                elif len(digits) == 11 and digits[0] == '1':
                    return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
                return phone

        # Format based on country
        if parsed.country_code == 1:  # US/Canada
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            )
        else:
            # International format for non-US numbers
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )

    except phonenumbers.NumberParseException:
        # If parsing fails, try basic formatting for 10-digit numbers
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return phone


def validate_address_usps(
    street: str,
    city: str,
    state: str,
    zip_code: str,
    usps_user_id: Optional[str] = None
) -> dict:
    """
    Validate and standardize a US address using USPS Web Tools API.

    Args:
        street: Street address (e.g., "123 Main St")
        city: City name
        state: State code (e.g., "CA", "NY")
        zip_code: ZIP code (5 or 9 digits)
        usps_user_id: USPS Web Tools User ID (or set USPS_USER_ID env var)

    Returns:
        dict with keys:
            - valid: bool
            - address: formatted address string (if valid)
            - street: standardized street
            - city: standardized city
            - state: standardized state
            - zip5: 5-digit ZIP
            - zip4: 4-digit ZIP extension (if available)
            - error: error message (if invalid)
    """
    user_id = usps_user_id or os.environ.get('USPS_USER_ID')

    if not user_id:
        return {
            'valid': False,
            'error': 'USPS_USER_ID not configured',
            'address': f"{street}, {city}, {state} {zip_code}".strip(', ')
        }

    # Build the XML request
    xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<AddressValidateRequest USERID="{user_id}">
    <Revision>1</Revision>
    <Address ID="0">
        <Address1></Address1>
        <Address2>{street}</Address2>
        <City>{city}</City>
        <State>{state}</State>
        <Zip5>{zip_code[:5] if zip_code else ''}</Zip5>
        <Zip4>{zip_code[6:10] if len(zip_code) > 5 else ''}</Zip4>
    </Address>
</AddressValidateRequest>"""

    try:
        response = requests.get(
            'https://secure.shippingapis.com/ShippingAPI.dll',
            params={
                'API': 'Verify',
                'XML': xml_request
            },
            timeout=10
        )
        response.raise_for_status()

        # Parse the XML response
        root = ET.fromstring(response.text)

        # Check for errors
        error = root.find('.//Error')
        if error is not None:
            error_desc = error.find('Description')
            return {
                'valid': False,
                'error': error_desc.text if error_desc is not None else 'Unknown error',
                'address': f"{street}, {city}, {state} {zip_code}".strip(', ')
            }

        # Extract validated address
        address = root.find('.//Address')
        if address is None:
            return {
                'valid': False,
                'error': 'No address in response',
                'address': f"{street}, {city}, {state} {zip_code}".strip(', ')
            }

        # USPS returns Address2 as the street address (Address1 is apt/suite)
        addr1 = address.find('Address1')
        addr2 = address.find('Address2')
        city_elem = address.find('City')
        state_elem = address.find('State')
        zip5 = address.find('Zip5')
        zip4 = address.find('Zip4')

        street_parts = []
        if addr2 is not None and addr2.text:
            street_parts.append(addr2.text)
        if addr1 is not None and addr1.text:
            street_parts.append(addr1.text)

        validated_street = ', '.join(street_parts)
        validated_city = city_elem.text if city_elem is not None else city
        validated_state = state_elem.text if state_elem is not None else state
        validated_zip5 = zip5.text if zip5 is not None else zip_code[:5]
        validated_zip4 = zip4.text if zip4 is not None and zip4.text else ''

        # Build the full ZIP
        full_zip = validated_zip5
        if validated_zip4:
            full_zip = f"{validated_zip5}-{validated_zip4}"

        # Build formatted address
        formatted_address = f"{validated_street}, {validated_city}, {validated_state} {full_zip}"

        return {
            'valid': True,
            'address': formatted_address,
            'street': validated_street,
            'city': validated_city,
            'state': validated_state,
            'zip5': validated_zip5,
            'zip4': validated_zip4,
        }

    except requests.RequestException as e:
        return {
            'valid': False,
            'error': f'Request failed: {str(e)}',
            'address': f"{street}, {city}, {state} {zip_code}".strip(', ')
        }
    except ET.ParseError as e:
        return {
            'valid': False,
            'error': f'XML parse error: {str(e)}',
            'address': f"{street}, {city}, {state} {zip_code}".strip(', ')
        }


def format_address(
    street: str = "",
    apt: str = "",
    city: str = "",
    state: str = "",
    zip_code: str = "",
    country: str = "",
    validate_us: bool = True,
    usps_user_id: Optional[str] = None
) -> str:
    """
    Format and optionally validate an address.

    For US addresses (country is empty, "US", "USA", or "United States"),
    will attempt USPS validation if enabled and credentials available.

    For international addresses, returns a formatted string without validation.

    Args:
        street: Street address
        apt: Apartment/floor/unit
        city: City
        state: State/province
        zip_code: ZIP/postal code
        country: Country name
        validate_us: Whether to validate US addresses via USPS
        usps_user_id: USPS User ID (or set USPS_USER_ID env var)

    Returns:
        Formatted address string
    """
    # Determine if this is a US address
    country_lower = country.lower().strip() if country else ""
    is_us = country_lower in ("", "us", "usa", "united states", "united states of america")

    # Combine street and apt
    full_street = street.strip() if street else ""
    if apt and apt.strip():
        full_street = f"{full_street}, {apt.strip()}"

    # Try USPS validation for US addresses
    if is_us and validate_us and full_street and (city or zip_code):
        result = validate_address_usps(
            street=full_street,
            city=city or "",
            state=state or "",
            zip_code=zip_code or "",
            usps_user_id=usps_user_id
        )
        if result.get('valid'):
            return result['address']
        # If validation failed but we have address components, fall through to manual formatting

    # Manual formatting
    parts = []

    if full_street:
        parts.append(full_street)

    # City, State ZIP
    city_state_zip = []
    if city:
        city_state_zip.append(city.strip())
    if state:
        if city_state_zip:
            city_state_zip[-1] = f"{city_state_zip[-1]}, {state.strip()}"
        else:
            city_state_zip.append(state.strip())
    if zip_code:
        if city_state_zip:
            city_state_zip[-1] = f"{city_state_zip[-1]} {zip_code.strip()}"
        else:
            city_state_zip.append(zip_code.strip())

    if city_state_zip:
        parts.append(' '.join(city_state_zip))

    # Add country for international addresses
    if country and not is_us:
        parts.append(country.strip())

    return ', '.join(parts)


if __name__ == "__main__":
    # Test phone formatting
    test_phones = [
        "4404634902",
        "(706) 307-0708",
        "19549951222",
        "+1 555-123-4567",
        "+91 98765 43210",  # India
    ]

    print("Phone Formatting Tests:")
    print("-" * 40)
    for phone in test_phones:
        formatted = format_phone_number(phone)
        print(f"  {phone:20} -> {formatted}")

    # Test address formatting (without USPS validation)
    print("\nAddress Formatting Tests (no USPS):")
    print("-" * 40)

    test_addresses = [
        {"street": "123 Main St", "city": "New York", "state": "NY", "zip_code": "10001"},
        {"street": "456 Oak Ave", "apt": "Apt 2B", "city": "Los Angeles", "state": "CA", "zip_code": "90001"},
        {"street": "10 Downing St", "city": "London", "country": "United Kingdom"},
    ]

    for addr in test_addresses:
        formatted = format_address(**addr, validate_us=False)
        print(f"  {formatted}")
