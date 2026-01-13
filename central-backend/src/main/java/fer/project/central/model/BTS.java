package fer.project.central.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
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

    @NotBlank(message = "BTS ID is required")
    @Column(name = "bts_id", nullable = false, length = 20)
    private String btsId;

    @NotBlank(message = "LAC is required")
    @Column(nullable = false, length = 10)
    private String lac;

    @NotNull(message = "Location X is required")
    @Column(name = "location_x", nullable = false)
    private BigDecimal locationX;

    @NotNull(message = "Location Y is required")
    @Column(name = "location_y", nullable = false)
    private BigDecimal locationY;

    @NotBlank(message = "Status is required")
    @Column(name = "status", length = 20)
    private String status;

    @NotNull(message = "Max capacity is required")
    @Min(value = 0, message = "Max capacity must be non-negative")
    @Column(name = "max_capacity")
    private Integer maxCapacity;

    @NotNull(message = "Current load is required")
    @Min(value = 0, message = "Current load must be non-negative")
    @Column(name = "current_load")
    private Integer currentLoad;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
