import React, { useMemo, useRef, useEffect, useState } from 'react';
import { toJalaali } from 'jalaali-js';
import MultiRangeSlider, { RangeSection } from '@/components/ui/MultiRangeSlider';
import TripItemCard from '@/components/TripItemCard';
import { TripItemWithDay } from '@/types/trip';

interface TimelineProps {
    title: string;
    items: TripItemWithDay[];
    totalDays: number;
    onItemTimeChange: (itemId: number, startTime: string, endTime: string) => void;
    onDeleteItem: (itemId: number) => void;
    onSuggestAlternative: (itemId: number) => void;
    color: string;
}

// Constants for timeline visualization
const MINUTES_PER_PIXEL = 0.3; // 0.5 minute per pixel (larger timeline)
const CARD_MAX_WIDTH = 500;
// (timeline spans `totalDays` so start/end constants not needed)

const Timeline: React.FC<TimelineProps> = ({
    title,
    items,
    totalDays,
    onItemTimeChange,
    onDeleteItem,
    onSuggestAlternative,
    color,
}) => {
    // Convert time string (HH:MM) and day to minutes from trip start
    const timeToMinutesFromTripStart = (time: string, dayNumber: number): number => {
        const [hours, minutes] = time.split(':').map(Number);
        const minutesInDay = hours * 60 + minutes;
        const dayOffset = (dayNumber - 1) * 24 * 60; // Convert day to minutes
        return dayOffset + minutesInDay;
    };

    // Convert minutes from trip start to time string (HH:MM)
    const minutesToTime = (minutes: number): string => {
        const minutesInDay = minutes % (24 * 60);
        const hours = Math.floor(minutesInDay / 60);
        const mins = minutesInDay % 60;
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    };

    // Calculate total timeline in minutes (all days)
    const totalMinutes = totalDays * 24 * 60;

    // Calculate total timeline width in pixels
    const timelineWidth = totalMinutes / MINUTES_PER_PIXEL;

    // Convert items to range sections
    const rangeSections: RangeSection[] = useMemo(() => {
        return items.map((item) => ({
            start: timeToMinutesFromTripStart(item.start_time, item.day_number),
            end: timeToMinutesFromTripStart(item.end_time, item.day_number),
        }));
    }, [items, totalDays]);

    // Handle range changes
    const handleRangeChange = (sections: RangeSection[]) => {
        sections.forEach((section, index) => {
            const item = items[index];
            if (item) {
                const newStartTime = minutesToTime(section.start);
                const newEndTime = minutesToTime(section.end);

                if (newStartTime !== item.start_time || newEndTime !== item.end_time) {
                    onItemTimeChange(item.id, newStartTime, newEndTime);
                }
            }
        });
    };

    // Calculate card positions and widths
    const cardPositions = useMemo(() => {
        return items.map((item) => {
            const startMinutes = timeToMinutesFromTripStart(item.start_time, item.day_number);
            const endMinutes = timeToMinutesFromTripStart(item.end_time, item.day_number);
            const durationMinutes = endMinutes - startMinutes;
            // Use exact same formula for both width and position
            const width = Math.min(durationMinutes / MINUTES_PER_PIXEL, CARD_MAX_WIDTH);
            // RTL: position from left based on distance from max time
            const translateX = (totalMinutes - startMinutes) / MINUTES_PER_PIXEL - width;

            return { width, translateX };
        });
    }, [items, totalDays]);

    const trackContainerRef = useRef<HTMLDivElement | null>(null);
    const innerTrackRef = useRef<HTMLDivElement | null>(null);
    const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
    const [visibleDay, setVisibleDay] = useState<number>(1);
    const rafRef = useRef<number | null>(null);

    // Scroll helpers
    const scrollToCard = (index: number) => {
        if (index < 0 || index >= items.length) return;
        const cardElement = cardRefs.current[index];
        if (cardElement) {
            // Save current window scroll position
            const windowScrollY = window.scrollY;
            cardElement.scrollIntoView({ behavior: 'smooth', inline: 'center' });
            // Immediately restore vertical scroll
            window.scrollTo({ top: windowScrollY, behavior: 'instant' });
        }
    };

    // On mount, scroll to first item (rightmost in RTL)
    useEffect(() => {
        if (items.length > 0) {
            // Small delay to ensure layout is ready
            setTimeout(() => {
                const cardElement = cardRefs.current[0];
                if (cardElement) {
                    const windowScrollY = window.scrollY;
                    cardElement.scrollIntoView({ behavior: 'auto', inline: 'center' });
                    window.scrollTo({ top: windowScrollY, behavior: 'instant' });
                }
            }, 100);
        }
    }, [items.length]);

    // Update visible day based on scroll position (center of container)
    useEffect(() => {
        const container = trackContainerRef.current;
        const inner = innerTrackRef.current;
        if (!container || !inner) return;

        const update = () => {
            const containerRect = container.getBoundingClientRect();
            const innerRect = inner.getBoundingClientRect();
            const containerWidth = containerRect.width;
            // center position in viewport relative to inner track left
            const centerX = containerRect.left + containerWidth / 2 - innerRect.left;
            // RTL mapping: pixel x corresponds to time = totalMinutes - x * MINUTES_PER_PIXEL
            let minutes = Math.round(totalMinutes - centerX * MINUTES_PER_PIXEL);
            if (minutes < 0) minutes = 0;
            if (minutes > totalMinutes) minutes = totalMinutes;
            const day = Math.floor(minutes / (24 * 60)) + 1;
            setVisibleDay(day);
            rafRef.current = null;
        };

        const onScroll = () => {
            if (rafRef.current != null) return;
            rafRef.current = window.requestAnimationFrame(update) as unknown as number;
        };

        // initial set
        update();

        container.addEventListener('scroll', onScroll, { passive: true });
        return () => {
            container.removeEventListener('scroll', onScroll);
            if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
        };
    }, [totalMinutes]);

    // Helper component to render visible day label with Jalali date
    interface VisibleDayLabelProps {
        visibleDay: number;
        items: TripItemWithDay[];
    }

    const persianWeekdays = [
        'یک‌شنبه',
        'دوشنبه',
        'سه‌شنبه',
        'چهارشنبه',
        'پنج‌شنبه',
        'جمعه',
        'شنبه',
    ];

    const VisibleDayLabel: React.FC<VisibleDayLabelProps> = ({ visibleDay, items }) => {
        // Try to find an item that matches the visible day
        let dateStr = items.find((i) => i.day_number === visibleDay)?.date;

        // If not found, derive from first item date + offset
        if (!dateStr && items.length > 0) {
            const first = items[0];
            const base = new Date(first.date);
            const dayOffset = visibleDay - first.day_number;
            const target = new Date(base);
            target.setDate(target.getDate() + dayOffset);
            dateStr = target.toISOString();
        }

        if (!dateStr) {
            return (
                <span className="inline-block bg-persian-blue text-white px-3 py-1 rounded shadow text-sm text-gray-700">{`روز ${visibleDay}`}</span>
            );
        }

        const gDate = new Date(dateStr);
        const weekday = persianWeekdays[gDate.getDay()];
        const { jy, jm, jd } = toJalaali(gDate.getFullYear(), gDate.getMonth() + 1, gDate.getDate());
        const jmStr = jm.toString().padStart(2, '0');
        const jdStr = jd.toString().padStart(2, '0');

        return (
            <span className="inline-block bg-persian-blue text-white px-3 py-1 rounded shadow text-sm text-gray-700">{`روز ${visibleDay} - ${weekday} ${jmStr}/${jdStr}`}</span>
        );
    };

    if (items.length === 0) return null;

    return (
        <div className="mb-12">
            {/* Timeline Header */}
            <div className="mb-3 text-center pb-1 border-b-2 border-gray-200">
                <h3 className="text-xl font-bold text-gray-800">{title}</h3>
            </div>

            {/* Visible Day (updates on scroll) */}
            <div className="mb-4 text-center">
                <VisibleDayLabel visibleDay={visibleDay} items={items} />
            </div>

            {/* Timeline Track */}
            <div className="relative -me-[150px] -ms-[150px]" style={{ overflowX: 'auto', overflowY: 'hidden' }} ref={trackContainerRef}>
                <div ref={innerTrackRef} style={{ width: `${timelineWidth}px`, minWidth: '100%', position: 'relative' }}>
                    {/* Cards Container */}
                    <div className="relative mb-4" style={{ height: '240px' }}>
                        {items.map((item, index) => {
                            const { width, translateX } = cardPositions[index];
                            const showArrows = true;
                            return (
                                <div
                                    key={item.id}
                                    ref={(el) => { cardRefs.current[index] = el; }}
                                    className="absolute top-0 left-0"
                                    style={{
                                        transform: `translateX(${translateX}px)`,
                                        transition: 'transform 0.2s ease',
                                        width: `${Math.min(width, CARD_MAX_WIDTH)}px`,
                                    }}
                                >
                                    <div
                                        onMouseEnter={() => setHoveredIndex(index)}
                                        onMouseLeave={() => setHoveredIndex((v) => (v === index ? null : v))}
                                        className="relative"
                                    >
                                        {index < items.length - 1 && (
                                            <button
                                                onClick={() => scrollToCard(index + 1)}
                                                className={`absolute -left-8 top-1/2 transform -translate-y-1/2 bg-white border hover:cursor-pointer border-gray-300 rounded-full w-7 h-7 flex items-center justify-center shadow-sm transition-opacity hover:bg-gray-50 z-10 ${showArrows ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                                                aria-label="next"
                                            >
                                                <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                                </svg>
                                            </button>
                                        )}

                                        <TripItemCard
                                            item={item}
                                            width={width}
                                            maxWidth={CARD_MAX_WIDTH}
                                            onDelete={onDeleteItem}
                                            onSuggestAlternative={onSuggestAlternative}
                                        />

                                        {index > 0 && (
                                            <button
                                                onClick={() => scrollToCard(index - 1)}
                                                className={`absolute -right-8 top-1/2 transform -translate-y-1/2 bg-white  hover:cursor-pointer border-gray-300 rounded-full w-7 h-7 flex items-center justify-center shadow-sm transition-opacity hover:bg-gray-50 z-10 ${showArrows ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                                                aria-label="prev"
                                            >
                                                <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                </svg>
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Slider with custom thumbs showing time */}
                    <MultiRangeSlider
                        sections={rangeSections}
                        min={0}
                        max={totalMinutes}
                        step={15}
                        onChange={() => { }}
                        activeColor={color}
                        gapColor="#e2e8f0"
                        renderThumb={(params: any) => {
                            const item = items[params.sectionIndex];
                            const time = params.isStartThumb ? item?.start_time : item?.end_time;

                            return (
                                <div
                                    {...params.props}
                                    key={params.props.key}
                                    style={{
                                        ...params.props.style,
                                        height: '32px',
                                        width: '32px',
                                        borderRadius: '50%',
                                        backgroundColor: '#FFF',
                                        boxShadow: '0px 2px 8px rgba(0,0,0,0.25)',
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        cursor: 'grab',
                                        outline: 'none',
                                        border: `2px solid ${color}`,
                                    }}
                                >
                                    <div
                                        className="absolute top-full mt-2 text-xs font-semibold text-gray-700 whitespace-nowrap"
                                        style={{ pointerEvents: 'none' }}
                                    >
                                        {time}
                                    </div>
                                </div>
                            );
                        }}
                    />

                    {/* Hourly markers across whole timeline */}
                    <div style={{ position: 'relative', height: 28, marginTop: 8 }}>
                        {Array.from({ length: totalMinutes / 60 + 1 }, (_, h) => h).map((hour) => {
                            const rightPercent = (hour * 60) / totalMinutes * 100;
                            const label = () => {
                                // For multi-day timeline, show day + hour when needed
                                if (hour >= 24) {
                                    const day = Math.floor(hour / 24) + 1;
                                    const hourOfDay = hour % 24;
                                    return `${hourOfDay.toString().padStart(2, '0')}:00`;
                                }
                                return `${hour.toString().padStart(2, '0')}:00`;
                            };

                            return (
                                <div key={hour} style={{ position: 'absolute', right: `${rightPercent}%`, transform: 'translateX(50%)', textAlign: 'center' }}>
                                    <div style={{ height: 6, width: 1, background: '#cbd5e1', margin: '0 auto' }} />
                                    <div className="text-xs text-gray-400 mt-1">{label()}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Timeline;
