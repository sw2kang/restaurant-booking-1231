import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from booking_scheduler import BookingScheduler
from schedule import Schedule

CUSTOMER = Mock()
CUSTOMER.get_email.return_value = None
CUSTOMER.phone_number = '010202010'
CUSTOMER_WITH_MAIL = Mock()
CUSTOMER_WITH_MAIL.get_email.return_value = "mock@mmm.ccc"
CUSTOMER_WITH_MAIL.phone_number = '010202010'
NOT_ON_HOUR = datetime.strptime("2024/03/26 08:05", "%Y/%m/%d %H:%M")
ON_HOUR = datetime.strptime("2024/03/26 08:00", "%Y/%m/%d %H:%M")

UNDER_CAPACITY = 1
CAPACITY_PER_HOUR = 3


class BookingSchedulerTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)
        self.sms_sender = Mock()
        self.mail_sender = Mock()
        self.booking_scheduler.set_sms_sender(self.sms_sender)
        self.booking_scheduler.set_mail_sender(self.mail_sender)

    def test_예약은_정시에만_가능하다_정시가_아닌경우_예약불가(self):
        schedule = Schedule(NOT_ON_HOUR, UNDER_CAPACITY, CUSTOMER)

        with self.assertRaises(ValueError):
            self.booking_scheduler.add_schedule(schedule)

    def test_예약은_정시에만_가능하다_정시인_경우_예약가능(self):
        schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER)

        self.booking_scheduler.add_schedule(schedule)

        self.assertTrue(self.booking_scheduler.has_schedule(schedule))

    def test_시간대별_인원제한이_있다_같은_시간대에_Capacity_초과할_경우_예외발생(self):
        schedule = Schedule(ON_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        with self.assertRaises(ValueError) as context:
            schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER)
            self.booking_scheduler.add_schedule(schedule)

        self.assertEqual("Number of people is over restaurant capacity per hour", str(context.exception))

    def test_시간대별_인원제한이_있다_같은_시간대가_다르면_Capacity_차있어도_스케쥴_추가_성공(self):
        schedule = Schedule(ON_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        different_hour = ON_HOUR + timedelta(hours=1)
        schedule = Schedule(different_hour, UNDER_CAPACITY, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        self.assertTrue(self.booking_scheduler.has_schedule(schedule))

    def test_예약완료시_SMS는_무조건_발송(self):
        schedule = Schedule(ON_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        self.assertTrue(self.sms_sender.is_send_method_is_called())

    def test_이메일이_없는_경우에는_이메일_미발송(self):
        schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER)

        self.booking_scheduler.add_schedule(schedule)

        self.mail_sender.send_mail.assert_not_called()

    def test_이메일이_있는_경우에는_이메일_발송(self):
        schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)

        self.booking_scheduler.add_schedule(schedule)

        self.mail_sender.send_mail.assert_called_once()

    @patch.object(BookingScheduler, 'get_now', return_value=datetime.strptime("2024/03/24 08:00", "%Y/%m/%d %H:%M"))
    def test_현재날짜가_일요일인_경우_예약불가_예외처리(self, mock):
        with self.assertRaises(ValueError):
            new_schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)
            self.booking_scheduler.add_schedule(new_schedule)
            self.fail()

    @patch.object(BookingScheduler, 'get_now', return_value=datetime.strptime("2024/03/25 08:00", "%Y/%m/%d %H:%M"))
    def test_현재날짜가_일요일이_아닌경우_예약가능(self, mock):
        new_schedule = Schedule(ON_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)
        self.booking_scheduler.add_schedule(new_schedule)
        self.assertTrue(self.booking_scheduler.has_schedule(new_schedule))


if __name__ == '__main__':
    unittest.main()
