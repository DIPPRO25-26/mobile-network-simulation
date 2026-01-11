package fer.project.central.service;

import fer.project.central.model.CDRRecord;
import fer.project.central.model.UserEventRequest;
import fer.project.central.model.UserEventResponse;
import fer.project.central.repository.CDRRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.util.Optional;

/**
 * Service for handling user events from BTS
 * 
 * MVP Implementation - basic functionality
 * 
 * TODO for team:
 * - Add Redis caching for recent user locations
 * - Add async processing for high load scenarios
 * - Implement batch processing for multiple events
 * - Add metrics/monitoring
 * - Error handling improvements
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final CDRRepository cdrRepository;

    /**
     * Process user event from BTS
     * Creates CDR record and returns previous location
     */
    @Transactional
    public UserEventResponse processUserEvent(UserEventRequest request) {
        log.debug("Processing user event for IMEI: {}, BTS: {}", request.getImei(), request.getBtsId());

        // Find previous location
        Optional<CDRRecord> previousRecordOpt = cdrRepository
                .findFirstByImeiOrderByTimestampArrivalDesc(request.getImei());

        // Create new CDR record
        CDRRecord cdrRecord = createCDRRecord(request, previousRecordOpt.orElse(null));
        CDRRecord savedRecord = cdrRepository.save(cdrRecord);

        // Update previous record's departure time
        previousRecordOpt.ifPresent(prev -> {
            prev.setTimestampDeparture(request.getTimestamp());
            cdrRepository.save(prev);
        });

        log.info("Created CDR record ID: {} for IMEI: {}", savedRecord.getId(), request.getImei());

        // Build response with previous location
        UserEventResponse.PreviousLocation previousLocation = previousRecordOpt
                .map(record -> new UserEventResponse.PreviousLocation(
                        record.getBtsId(),
                        record.getLac(),
                        record.getTimestampArrival()
                ))
                .orElse(null);

        return UserEventResponse.success(previousLocation, savedRecord.getId());
    }

    /**
     * Create CDR record from request
     */
    private CDRRecord createCDRRecord(UserEventRequest request, CDRRecord previousRecord) {
        CDRRecord record = new CDRRecord();
        record.setImei(request.getImei());
        record.setMcc(request.getMcc());
        record.setMnc(request.getMnc());
        record.setLac(request.getLac());
        record.setBtsId(request.getBtsId());
        record.setTimestampArrival(request.getTimestamp());

        if (request.getUserLocation() != null) {
            record.setUserLocationX(BigDecimal.valueOf(request.getUserLocation().getX()));
            record.setUserLocationY(BigDecimal.valueOf(request.getUserLocation().getY()));
        }

        // Set previous BTS if exists
        if (previousRecord != null) {
            record.setPreviousBtsId(previousRecord.getBtsId());
            
            // Calculate distance between previous and current location
            BigDecimal distance = calculateDistance(previousRecord, record);
            record.setDistance(distance);
            
            // Calculate duration at previous BTS (in seconds)
            Integer duration = calculateDuration(previousRecord, record);
            record.setDuration(duration);
            
            // Calculate speed based on distance and time difference
            record.setSpeed(calculateSpeed(distance, duration));
        }

        return record;
    }

    private BigDecimal calculateDistance(CDRRecord previous, CDRRecord current) {
        if (previous.getUserLocationX() == null || previous.getUserLocationY() == null ||
            current.getUserLocationX() == null || current.getUserLocationY() == null) {
            return BigDecimal.ZERO;
        }

        // Euclidean distance
        double x1 = previous.getUserLocationX().doubleValue();
        double y1 = previous.getUserLocationY().doubleValue();
        double x2 = current.getUserLocationX().doubleValue();
        double y2 = current.getUserLocationY().doubleValue();

        double distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        return BigDecimal.valueOf(distance).setScale(4, RoundingMode.HALF_UP);
    }

    private BigDecimal calculateSpeed(BigDecimal distance, Integer durationInSeconds) {
        if (durationInSeconds == null || durationInSeconds <= 0) {
            return BigDecimal.ZERO;
        }

        return distance.divide(BigDecimal.valueOf(durationInSeconds), 4, RoundingMode.HALF_UP);
    }

    private Integer calculateDuration(CDRRecord previous, CDRRecord current) {
        if (previous.getTimestampArrival() == null || current.getTimestampArrival() == null) {
            return 0;
        }

        long seconds = Duration.between(previous.getTimestampArrival(), previous.getTimestampDeparture()).getSeconds();
        return (int) seconds;
    }
}
