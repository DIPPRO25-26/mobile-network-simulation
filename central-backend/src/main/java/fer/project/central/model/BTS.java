package fer.project.central.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "bts_registry")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BTS {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "bts_id", nullable = false, length = 20)
    private String btsId;

    @Column(nullable = false, length = 10)
    private String lac;

    @Column(name = "location_x", nullable = false)
    private BigDecimal locationX;

    @Column(name = "location_y", nullable = false)
    private BigDecimal locationY;

    @Column(name = "status", length = 20)
    private String status;

    @Column(name = "max_capacity")
    private Integer maxCapacity;

    @Column(name = "current_load")
    private Integer currentLoad;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
