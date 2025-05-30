function loadSection(section) {
  const content = document.getElementById('mainContent');
  content.innerHTML = '<div class="spinner"></div><p>Loading...</p>';

  if (section === 'book_room') {
    fetch('/student_section/check_booking')
      .then(response => {
        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            content.innerHTML = '<p class="error">Session expired. Please <a href="/login">log in again</a>.</p>';
            return;
          }
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (!data) return; 
        if (data.rejected) {
          content.innerHTML = `
            <h2>Book a Room</h2>
            <p class="error">Your previous booking request was rejected by the admin.</p>
            <p>You can submit a new booking request below.</p>
          `;
          loadBookingForm();
        } else if (data.already_requested) {
          content.innerHTML = `
            <h2>Book a Room</h2>
            <p class="error">You already have a pending or approved booking.</p>
            <p><a href="#" onclick="loadSection('allocation')">View your allocation</a></p>
          `;
        } else {
          content.innerHTML = '<h2>Book a Room</h2>';
          loadBookingForm();
        }
      })
      .catch(error => {
        content.innerHTML = '<p class="error">Error checking booking status: ' + error.message + '</p>';
        console.error(error);
      });
  } else {
    let url;
    if (section === 'allocation') {
      url = '/my_allocation';
    } else if (section === 'complaint') {
      url = '/submit_complaint';
    } else {
      content.innerHTML = '<p class="error">Invalid section.</p>';
      return;
    }

    fetch(url)
      .then(response => {
        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            content.innerHTML = '<p class="error">Session expired. Please <a href="/login">log in again</a>.</p>';
            return;
          }
          throw new Error('Network response was not ok');
        }
        return response.text();
      })
      .then(html => {
        if (html) content.innerHTML = html;
      })
      .catch(error => {
        content.innerHTML = '<p class="error">Error loading section: ' + error.message + '</p>';
        console.error(error);
      });
  }
}

function loadBookingForm() {
  fetch('/student_section/get_rooms')
    .then(response => {
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          document.getElementById('mainContent').innerHTML = '<p class="error">Session expired. Please <a href="/login">log in again</a>.</p>';
          return;
        }
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(rooms => {
      if (!rooms) return; 
      if (rooms.length === 0) {
        document.getElementById('mainContent').innerHTML += '<p class="error">No rooms are currently available for booking.</p>';
        return;
      }

      let roomOptions = rooms.map(room => `
        <option value="${room.id}">
          ${room.room_number} (Beds Available: ${room.available_beds}/${room.max_capacity})
        </option>
      `).join('');

      const formHtml = `
        <form id="bookingForm" onsubmit="submitBooking(event)">
          <label for="name">Full Name:</label><br>
          <input type="text" id="name" name="name" placeholder="Enter your full name" required><br><br>

          <label for="email">Email:</label><br>
          <input type="email" id="email" name="email" placeholder="Enter your email" required><br><br>

          <label for="phone">Phone Number:</label><br>
          <input type="text" id="phone" name="phone" placeholder="Enter your phone number" required><br><br>

          <label for="room_id">Select Room:</label><br>
          <select id="room_id" name="room_id" required>
            <option value="">-- Select a Room --</option>
            ${roomOptions}
          </select><br><br>

          <label for="payment_method">Payment Method:</label><br>
          <select id="payment_method" name="payment_method" required>
            <option value="">-- Select Payment Method --</option>
            <option value="credit_card">Credit Card</option>
            <option value="upi">UPI</option>
            <option value="net_banking">Net Banking</option>
          </select><br><br>

          <button type="submit">Submit Booking Request</button>
        </form>
        <p id="formMessage"></p>
      `;
      document.getElementById('mainContent').insertAdjacentHTML('beforeend', formHtml);
    })
    .catch(error => {
      document.getElementById('mainContent').innerHTML += '<p class="error">Error loading rooms: ' + error.message + '</p>';
      console.error(error);
    });
}

function submitBooking(event) {
  event.preventDefault();
  const form = document.getElementById('bookingForm');
  const formData = new FormData(form);
  const message = document.getElementById('formMessage');

  fetch('/student_section/book_room', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          message.innerHTML = '<p class="error">Session expired. Please <a href="/login">log in again</a>.</p>';
          return;
        }
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (!data) return; 
      if (data.success) {
        message.innerHTML = '<p class="success">Room booking requested! Waiting for admin approval.</p>';
        form.reset();
        setTimeout(() => loadSection('allocation'), 2000);
      } else {
        message.innerHTML = `<p class="error">${data.message}</p>`;
      }
    })
    .catch(error => {
      message.innerHTML = '<p class="error">Error submitting booking: ' + error.message + '</p>';
      console.error(error);
    });
}