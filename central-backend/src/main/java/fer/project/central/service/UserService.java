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
import java.util.Optional;

/**
 * Service for handling user events from BTS
 * 
 * MVP Implementation - basic functionality
 * 
 * TODO for team:
 * - Implement distance calculation between BTS locations
 * - Implement speed calculation
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
        Optional<CDRRecord> previousRecord = cdrRepository
                .findFirstByImeiOrderByTimestampArrivalDesc(request.getImei());

        // Create new CDR record
        CDRRecord cdrRecord = createCDRRecord(request, previousRecord.orElse(null));
        CDRRecord savedRecord = cdrRepository.save(cdrRecord);

        log.info("Created CDR record ID: {} for IMEI: {}", savedRecord.getId(), request.getImei());

        // Build response with previous location
        UserEventResponse.PreviousLocation previousLocation = previousRecord
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
     * TODO: Calculate distance and speed
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
            
            // TODO: Calculate distance between previous and current location
            // record.setDistance(calculateDistance(previousRecord, record));
            
            // TODO: Calculate speed based on distance and time difference
            // record.setSpeed(calculateSpeed(previousRecord, record));
            
            // TODO: Calculate duration at previous BTS
            // record.setDuration(calculateDuration(previousRecord, record));
        }

        return record;
    }

    // TODO: Implement these utility methods
    /*
    private BigDecimal calculateDistance(CDRRecord previous, CDRRecord current) {
        // Use Euclidean distance or haversine formula
        return BigDecimal.ZERO;
    }

    private BigDecimal calculateSpeed(CDRRecord previous, CDRRecord current) {
        // speed = distance / time
        return BigDecimal.ZERO;
    }

    private Integer calculateDuration(CDRRecord previous, CDRRecord current) {
        // duration in seconds between timestamps
        return 0;
    }
    */
}
