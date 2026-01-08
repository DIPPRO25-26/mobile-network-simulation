package fer.project.central.repository;

import fer.project.central.model.CDRRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository for CDR Records
 * 
 * MVP Implementation - basic queries only
 * 
 * TODO for team:
 * - Add pagination support
 * - Add custom queries with filters (btsId, lac, time range)
 * - Add aggregation queries for analytics
 * - Implement @Query for complex searches
 * - Add sorting options
 */
@Repository
public interface CDRRepository extends JpaRepository<CDRRecord, Long> {

    /**
     * Find the most recent CDR record for a given IMEI
     * Used to get previous location of user
     */
    Optional<CDRRecord> findFirstByImeiOrderByTimestampArrivalDesc(String imei);

    /**
     * Find all CDR records for a specific IMEI
     * TODO: Add pagination
     */
    List<CDRRecord> findByImei(String imei);

    /**
     * Find CDR records by BTS ID
     * TODO: Add pagination and date range filters
     */
    List<CDRRecord> findByBtsId(String btsId);

    /**
     * Find CDR records within a time range
     * TODO: Optimize with indexes
     */
    @Query("SELECT c FROM CDRRecord c WHERE c.timestampArrival BETWEEN :start AND :end")
    List<CDRRecord> findByTimeRange(@Param("start") LocalDateTime start, 
                                     @Param("end") LocalDateTime end);

    // TODO: Add more custom queries as needed:
    // - findByLac
    // - findByMccAndMnc
    // - countByBtsId (for load analysis)
    // - findRecentTransitions (for anomaly detection)
}
