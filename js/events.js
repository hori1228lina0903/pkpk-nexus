// events.js
document.addEventListener('DOMContentLoaded', function() {
  console.log('events.js loaded');
  
  // カルーセルを使うか判定
  const eventsContainer = document.querySelector('.events-container');
  const useCarousel = eventsContainer ? eventsContainer.classList.contains('use-carousel') : false;
  console.log('useCarousel:', useCarousel);
  
  const jsonPath = '/data/all_events.json';
  
  fetch(jsonPath)
    .then(response => response.json())
    .then(events => {
      console.log('Loaded', events.length, 'events');
      
      const today = new Date();
      const monthMap = {
        'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
        'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
      };
      
      const ongoingEvents = [];
      const upcomingEvents = [];
      const pastEvents = [];
      
      events.forEach(event => {
        if (!event.date || event.date === '') {
          pastEvents.push(event);
          return;
        }
        
        const rangeMatch = event.date.match(/(\w+)\s+(\d+)\s*-\s*(\w+)\s+(\d+),\s*(\d{4})/);
        
        if (rangeMatch) {
          const startMonth = monthMap[rangeMatch[1]];
          const startDay = parseInt(rangeMatch[2]);
          const endMonth = monthMap[rangeMatch[3]];
          const endDay = parseInt(rangeMatch[4]);
          const year = parseInt(rangeMatch[5]);
          
          const startDate = new Date(year, startMonth, startDay);
          const endDate = new Date(year, endMonth, endDay);
          endDate.setHours(23, 59, 59, 999);
          
          if (today >= startDate && today <= endDate) {
            event.startDate = startDate;
            ongoingEvents.push(event);
          } else if (today < startDate) {
            event.startDate = startDate;
            upcomingEvents.push(event);
          } else {
            pastEvents.push(event);
          }
        } else {
          pastEvents.push(event);
        }
      });
      
      const getDateValue = (dateStr) => {
        if (!dateStr) return 0;
        const match = dateStr.match(/(\w+)\s+(\d+)(?:\s*-\s*\w+\s+\d+)?,\s*(\d{4})/);
        if (match) {
          const month = monthMap[match[1]];
          const day = parseInt(match[2]);
          const year = parseInt(match[3]);
          return new Date(year, month, day).getTime();
        }
        return 0;
      };
      
      ongoingEvents.sort((a, b) => getDateValue(b.date) - getDateValue(a.date));
      upcomingEvents.sort((a, b) => getDateValue(a.date) - getDateValue(b.date));
      pastEvents.sort((a, b) => getDateValue(b.date) - getDateValue(a.date));
      
      if (useCarousel) {
        displayEventsAsCarousel(ongoingEvents, upcomingEvents, pastEvents);
      } else {
        displayEventsAsList(ongoingEvents, upcomingEvents, pastEvents);
      }
      
      console.log('Ongoing:', ongoingEvents.length, 'Upcoming:', upcomingEvents.length, 'Past:', pastEvents.length);
    })
    .catch(error => {
      console.error('Failed to load events:', error);
      const ongoingContainer = document.querySelector('.ongoing-events-container');
      const upcomingContainer = document.querySelector('.upcoming-events-container');
      const pastContainer = document.querySelector('.past-events-container');
      if (ongoingContainer) ongoingContainer.innerHTML = '<p>Failed to load events.</p>';
      if (upcomingContainer) upcomingContainer.innerHTML = '<p>Failed to load events.</p>';
      if (pastContainer) pastContainer.innerHTML = '<p>Failed to load events.</p>';
    });
});

function isNewEvent(event) {
  if (!event.startDate) return false;
  const today = new Date();
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(today.getDate() - 7);
  return event.startDate >= oneWeekAgo && event.startDate <= today;
}

function getTypeBadgeInfo(type) {
  const typeMap = {
    'ranked_match': { name: 'Ranked', class: 'type-badge-ranked' },
    'drop_event': { name: 'Drop', class: 'type-badge-drop' },
    'mission': { name: 'Mission', class: 'type-badge-mission' },
    'premium_shop': { name: 'Premium', class: 'type-badge-premium' },
    'emblem_event': { name: 'Emblem', class: 'type-badge-emblem' },
    'release': { name: 'Release', class: 'type-badge-release' },
    'wonder_pick': { name: 'Wonder Pick', class: 'type-badge-wonder' },
    'celebration': { name: 'Celebration', class: 'type-badge-celebration' },
    'campaign': { name: 'Campaign', class: 'type-badge-campaign' },
    'sale': { name: 'Sale', class: 'type-badge-sale' },
    'mass_outbreak': { name: 'Mass Outbreak', class: 'type-badge-mass' },
    'rerun': { name: 'Rerun', class: 'type-badge-rerun' },
    'gift': { name: 'Gift', class: 'type-badge-gift' }
  };
  return typeMap[type] || { name: 'Event', class: 'type-badge-default' };
}

function displayEventsAsList(ongoingEvents, upcomingEvents, pastEvents) {
  const ongoingContainer = document.querySelector('.ongoing-events-container');
  if (ongoingContainer) {
    if (ongoingEvents.length === 0) {
      ongoingContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
    } else {
      let ongoingHtml = '';
      ongoingEvents.forEach(event => {
        const imagePath = event.key_visual || '/images/events/default_event.webp';
        const typeInfo = getTypeBadgeInfo(event.type);
        const newBadgeHtml = isNewEvent(event) ? '<div class="new-badge">NEW</div>' : '';
        ongoingHtml += `
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
                ${newBadgeHtml}
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        `;
      });
      ongoingContainer.innerHTML = ongoingHtml;
    }
  }
  
  const upcomingContainer = document.querySelector('.upcoming-events-container');
  if (upcomingContainer) {
    if (upcomingEvents.length === 0) {
      upcomingContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
    } else {
      let upcomingHtml = '';
      upcomingEvents.forEach(event => {
        const imagePath = event.key_visual || '/images/events/default_event.webp';
        const typeInfo = getTypeBadgeInfo(event.type);
        upcomingHtml += `
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        `;
      });
      upcomingContainer.innerHTML = upcomingHtml;
    }
  }
  
  const pastContainer = document.querySelector('.past-events-container');
  if (pastContainer) {
    if (pastEvents.length === 0) {
      pastContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
    } else {
      let pastHtml = '';
      pastEvents.forEach(event => {
        const imagePath = event.key_visual || '/images/events/default_event.webp';
        const typeInfo = getTypeBadgeInfo(event.type);
        pastHtml += `
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        `;
      });
      pastContainer.innerHTML = pastHtml;
    }
  }
}

function displayEventsAsCarousel(ongoingEvents, upcomingEvents, pastEvents) {
  console.log('カルーセル表示モード');
  
  // Ongoing Events カルーセル
  const ongoingContainer = document.querySelector('.ongoing-events-container');
  if (ongoingContainer && ongoingEvents.length > 0) {
    let ongoingHtml = `
      <div class="swiper ongoing-swiper">
        <div class="swiper-wrapper">
    `;
    ongoingEvents.forEach(event => {
      const imagePath = event.key_visual || '/images/events/default_event.webp';
      const typeInfo = getTypeBadgeInfo(event.type);
      const newBadgeHtml = isNewEvent(event) ? '<div class="new-badge">NEW</div>' : '';
      ongoingHtml += `
        <div class="swiper-slide">
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
                ${newBadgeHtml}
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        </div>
      `;
    });
    ongoingHtml += `
        </div>
        <div class="swiper-pagination"></div>
      </div>
    `;
    ongoingContainer.innerHTML = ongoingHtml;
  } else if (ongoingContainer && ongoingEvents.length === 0) {
    ongoingContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
  }
  
  // Upcoming Events カルーセル
  const upcomingContainer = document.querySelector('.upcoming-events-container');
  if (upcomingContainer && upcomingEvents.length > 0) {
    let upcomingHtml = `
      <div class="swiper upcoming-swiper">
        <div class="swiper-wrapper">
    `;
    upcomingEvents.forEach(event => {
      const imagePath = event.key_visual || '/images/events/default_event.webp';
      const typeInfo = getTypeBadgeInfo(event.type);
      upcomingHtml += `
        <div class="swiper-slide">
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        </div>
      `;
    });
    upcomingHtml += `
        </div>
        <div class="swiper-pagination"></div>
      </div>
    `;
    upcomingContainer.innerHTML = upcomingHtml;
  } else if (upcomingContainer && upcomingEvents.length === 0) {
    upcomingContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
  }
  
  // Past Events 通常表示
  const pastContainer = document.querySelector('.past-events-container');
  if (pastContainer) {
    if (pastEvents.length === 0) {
      pastContainer.innerHTML = '<p class="no-events-message">No events to display at this time.</p>';
    } else {
      let pastHtml = '';
      pastEvents.forEach(event => {
        const imagePath = event.key_visual || '/images/events/default_event.webp';
        const typeInfo = getTypeBadgeInfo(event.type);
        pastHtml += `
          <a href="${event.link}">
            <div class="event_item">
              <div class="event_image_wrapper">
                <img src="${imagePath}" alt="${event.title}" class="event_top">
              </div>
              <div class="event_bottom">
                <div class="event_meta">
                  <span class="type-badge ${typeInfo.class}">${typeInfo.name}</span>
                  <p class="event_date">${event.date}</p>
                </div>
                <p>${event.title}</p>
              </div>
            </div>
          </a>
        `;
      });
      pastContainer.innerHTML = pastHtml;
    }
  }
}