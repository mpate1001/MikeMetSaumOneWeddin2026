"""
Utility functions for formatting phone numbers and validating addresses.
"""

import os
import re
import time
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


def get_usps_oauth_token(consumer_key: str, consumer_secret: str) -> Optional[str]:
    """
    Get OAuth access token from USPS API.

    Args:
        consumer_key: USPS Consumer Key
        consumer_secret: USPS Consumer Secret

    Returns:
        Access token string, or None if failed
    """
    try:
        # USPS OAuth uses client credentials in body (not Basic Auth header)
        # Base URL is apis.usps.com (with 's'), not api.usps.com
        response = requests.post(
            'https://apis.usps.com/oauth2/v3/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': consumer_key,
                'client_secret': consumer_secret,
                'scope': 'addresses',
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()
        return data.get('access_token')
    except requests.RequestException as e:
        # Try to get more details from response
        error_detail = ""
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f" - {e.response.text[:100]}"
            except:
                pass
        print(f"      USPS OAuth error: {str(e)[:60]}{error_detail}")
        return None
    except Exception as e:
        print(f"      USPS OAuth unexpected error: {str(e)[:50]}")
        return None


# Cache the token to avoid getting a new one for each address
_usps_token_cache = {
    'token': None,
    'expires_at': 0
}


def get_cached_usps_token() -> Optional[str]:
    """Get USPS token, using cache if valid."""
    consumer_key = os.environ.get('USPS_CONSUMER_KEY')
    consumer_secret = os.environ.get('USPS_CONSUMER_SECRET')

    if not consumer_key or not consumer_secret:
        return None

    # Check if cached token is still valid (with 60s buffer)
    if _usps_token_cache['token'] and time.time() < _usps_token_cache['expires_at'] - 60:
        return _usps_token_cache['token']

    # Get new token
    token = get_usps_oauth_token(consumer_key, consumer_secret)
    if token:
        # USPS tokens typically last 1 hour (3600 seconds)
        _usps_token_cache['token'] = token
        _usps_token_cache['expires_at'] = time.time() + 3600

    return token


def validate_address_usps(
    street: str,
    city: str,
    state: str,
    zip_code: str,
) -> dict:
    """
    Validate and standardize a US address using USPS Addresses API (OAuth).

    Requires USPS_CONSUMER_KEY and USPS_CONSUMER_SECRET environment variables.

    Args:
        street: Street address (e.g., "123 Main St")
        city: City name
        state: State code (e.g., "CA", "NY")
        zip_code: ZIP code (5 or 9 digits)

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
    fallback_address = f"{street}, {city}, {state} {zip_code}".strip(', ')

    # Get OAuth token
    token = get_cached_usps_token()
    if not token:
        return {
            'valid': False,
            'error': 'USPS credentials not configured or token failed',
            'address': fallback_address
        }

    try:
        # Build query parameters for the Addresses API
        params = {
            'streetAddress': street,
            'city': city,
            'state': state,
        }
        if zip_code:
            params['ZIPCode'] = zip_code[:5]

        response = requests.get(
            'https://apis.usps.com/addresses/v3/address',
            params=params,
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
            },
            timeout=10
        )

        # Handle different response codes
        if response.status_code == 404:
            return {
                'valid': False,
                'error': 'Address not found',
                'address': fallback_address
            }

        if response.status_code == 400:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Invalid request')
            return {
                'valid': False,
                'error': error_msg,
                'address': fallback_address
            }

        response.raise_for_status()
        data = response.json()

        # Extract the address from response
        addr = data.get('address', {})

        validated_street = addr.get('streetAddress', street)
        if addr.get('secondaryAddress'):
            validated_street += f", {addr['secondaryAddress']}"

        validated_city = addr.get('city', city)
        validated_state = addr.get('state', state)
        validated_zip5 = addr.get('ZIPCode', zip_code[:5] if zip_code else '')
        validated_zip4 = addr.get('ZIPPlus4', '')

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
            'address': fallback_address
        }
    except (KeyError, ValueError) as e:
        return {
            'valid': False,
            'error': f'Parse error: {str(e)}',
            'address': fallback_address
        }


def is_usps_configured() -> bool:
    """Check if USPS API credentials are configured."""
    return bool(os.environ.get('USPS_CONSUMER_KEY') and os.environ.get('USPS_CONSUMER_SECRET'))


def format_address(
    street: str = "",
    apt: str = "",
    city: str = "",
    state: str = "",
    zip_code: str = "",
    country: str = "",
    validate_us: bool = True,
) -> str:
    """
    Format and optionally validate an address.

    For US addresses (country is empty, "US", "USA", or "United States"),
    will attempt USPS validation if enabled and credentials available.
    Requires USPS_CONSUMER_KEY and USPS_CONSUMER_SECRET env vars.

    For international addresses, returns a formatted string without validation.

    Args:
        street: Street address
        apt: Apartment/floor/unit
        city: City
        state: State/province
        zip_code: ZIP/postal code
        country: Country name
        validate_us: Whether to validate US addresses via USPS

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
    if is_us and validate_us and is_usps_configured() and full_street and (city or zip_code):
        result = validate_address_usps(
            street=full_street,
            city=city or "",
            state=state or "",
            zip_code=zip_code or "",
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
