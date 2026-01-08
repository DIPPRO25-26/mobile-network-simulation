package fer.project.central.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * CDR (Call Detail Record) Entity
 * 
 * MVP Implementation - stores basic user transition data
 * 
 * TODO for team:
 * - Add indexes for performance optimization
 * - Add composite keys if needed
 * - Implement audit fields (@CreatedDate, @LastModifiedDate)
 * - Add validation constraints
 */
@Entity
@Table(name = "cdr_records")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CDRRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 15)
    private String imei;

    @Column(nullable = false, length = 3)
    private String mcc;

    @Column(nullable = false, length = 3)
    private String mnc;

    @Column(nullable = false, length = 10)
    private String lac;

    @Column(name = "bts_id", nullable = false, length = 20)
    private String btsId;

    @Column(name = "previous_bts_id", length = 20)
    private String previousBtsId;

    @Column(name = "timestamp_arrival", nullable = false)
    private LocalDateTime timestampArrival;

    @Column(name = "timestamp_departure")
    private LocalDateTime timestampDeparture;

    @Column(name = "user_location_x")
    private BigDecimal userLocationX;

    @Column(name = "user_location_y")
    private BigDecimal userLocationY;

    // TODO: Calculate these fields in service layer
    private BigDecimal distance;
    private BigDecimal speed;
    private Integer duration; // in seconds

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
